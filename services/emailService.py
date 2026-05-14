import os
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

_PRIMARY = "#8B3A5E"
_DARK    = "#5A1F3A"
_GOLD    = "#FFC107"


def _base_template(content: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  body{{margin:0;padding:0;background:#f5f0f3;font-family:Arial,sans-serif;}}
  .wrap{{max-width:600px;margin:32px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08);}}
  .header{{background:{_DARK};padding:28px 32px;text-align:center;}}
  .header h1{{margin:0;color:#fff;font-size:22px;font-weight:700;letter-spacing:.5px;}}
  .header p{{margin:4px 0 0;color:rgba(255,255,255,.75);font-size:13px;}}
  .body{{padding:32px;color:#333;line-height:1.6;}}
  .body h2{{color:{_PRIMARY};font-size:18px;margin:0 0 12px;}}
  .info-box{{background:#faf6f8;border-left:4px solid {_PRIMARY};border-radius:6px;padding:16px 20px;margin:20px 0;}}
  .info-row{{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #ede0e8;font-size:14px;}}
  .info-row:last-child{{border-bottom:none;}}
  .info-label{{color:#888;}}
  .info-value{{font-weight:600;color:#333;}}
  .badge{{display:inline-block;padding:5px 14px;border-radius:20px;font-size:13px;font-weight:700;}}
  .badge-confirmada{{background:#e8f5e9;color:#2e7d32;}}
  .badge-cancelada{{background:#ffebee;color:#c62828;}}
  .badge-reagenda{{background:#fff8e1;color:#f57f17;}}
  .badge-completada{{background:#e3f2fd;color:#1565c0;}}
  .btn{{display:inline-block;background:{_PRIMARY};color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:700;font-size:14px;margin-top:20px;}}
  .footer{{background:#f9f4f7;padding:20px 32px;text-align:center;font-size:12px;color:#aaa;border-top:1px solid #ede0e8;}}
  .divider{{border:none;border-top:1px solid #ede0e8;margin:24px 0;}}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>✨ Shirley Buenaño</h1>
    <p>Centro de Estética, Belleza y Moda</p>
  </div>
  <div class="body">{content}</div>
  <div class="footer">
    Este correo es generado automáticamente. Por favor no respondas a este mensaje.<br>
    © 2026 Shirley Buenaño · Centro de Estética
  </div>
</div>
</body></html>"""


def _appt_rows(appt: dict) -> str:
    rows = [
        ("Servicio",     appt.get("service_name", "—")),
        ("Especialista", appt.get("worker_name",  "—")),
        ("Fecha",        appt.get("date",         "—")),
        ("Horario",      f"{appt.get('start_time','—')} – {appt.get('end_time','—')}"),
        ("Total",        f"${appt.get('total_price', 0):.2f}"),
    ]
    if appt.get("promotion_name"):
        rows.append(("Combo", appt["promotion_name"]))
    return "".join(
        f'<div class="info-row"><span class="info-label">{k}</span>'
        f'<span class="info-value">{v}</span></div>'
        for k, v in rows
    )


# ── Plantillas ─────────────────────────────────────────────────────────────────

def _html_welcome(first_name: str) -> str:
    content = f"""
<h2>¡Bienvenida, {first_name}! 🎉</h2>
<p>Nos alegra tenerte en nuestra comunidad. En <strong>Shirley Buenaño</strong> encontrarás
los mejores servicios de estética, belleza y moda, disponibles para ti en cualquier momento.</p>
<div class="info-box" style="border-left-color:{_GOLD};">
  <p style="margin:0;font-size:14px;">🌟 <strong>¿Qué puedes hacer ahora?</strong></p>
  <ul style="margin:8px 0 0;padding-left:20px;font-size:14px;color:#555;">
    <li>Explorar nuestros servicios y promociones</li>
    <li>Agendar tu primera cita en minutos</li>
    <li>Pagar de forma segura con Payphone o comprobante</li>
  </ul>
</div>
<p>Si tienes alguna duda, no dudes en contactarnos. ¡Estamos para servirte!</p>
<a href="#" class="btn">Ver Servicios</a>
"""
    return _base_template(content)


def _html_appointment_confirmed(first_name: str, appt: dict) -> str:
    content = f"""
<h2>¡Tu cita ha sido confirmada! ✅</h2>
<p>Hola <strong>{first_name}</strong>, tu pago fue verificado y tu cita está confirmada.
¡Te esperamos!</p>
<div class="info-box">
  <span class="badge badge-confirmada">CONFIRMADA</span>
  <hr class="divider" style="margin:12px 0;">
  {_appt_rows(appt)}
</div>
<p style="font-size:13px;color:#888;">Recuerda llegar con al menos 5 minutos de anticipación.
Las citas canceladas no tienen devolución.</p>
"""
    return _base_template(content)


def _html_appointment_cancelled(first_name: str, appt: dict) -> str:
    reason = appt.get("cancel_reason", "")
    reason_html = f'<p style="font-size:13px;color:#c62828;"><strong>Motivo:</strong> {reason}</p>' if reason else ""
    content = f"""
<h2>Tu cita ha sido cancelada</h2>
<p>Hola <strong>{first_name}</strong>, te informamos que la siguiente cita fue cancelada:</p>
<div class="info-box">
  <span class="badge badge-cancelada">CANCELADA</span>
  <hr class="divider" style="margin:12px 0;">
  {_appt_rows(appt)}
</div>
{reason_html}
<p style="font-size:13px;color:#888;">Recuerda que las citas canceladas no tienen devolución.
Si tienes preguntas, contáctanos directamente.</p>
"""
    return _base_template(content)


def _html_reschedule_proposal(first_name: str, appt: dict) -> str:
    content = f"""
<h2>Tu especialista propone reagendar tu cita 📅</h2>
<p>Hola <strong>{first_name}</strong>, <strong>{appt.get('worker_name','tu especialista')}</strong>
ha solicitado reagendar tu cita de <strong>{appt.get('service_name','—')}</strong>.</p>

<div class="info-box">
  <p style="margin:0 0 8px;font-size:13px;color:#888;font-weight:600;">HORARIO ORIGINAL</p>
  <div class="info-row">
    <span class="info-label">Fecha</span>
    <span class="info-value">{appt.get('date','—')}</span>
  </div>
  <div class="info-row">
    <span class="info-label">Horario</span>
    <span class="info-value">{appt.get('start_time','—')} – {appt.get('end_time','—')}</span>
  </div>
</div>

<div class="info-box" style="border-left-color:{_GOLD};">
  <p style="margin:0 0 8px;font-size:13px;color:#f57f17;font-weight:600;">NUEVO HORARIO PROPUESTO</p>
  <div class="info-row">
    <span class="info-label">Fecha</span>
    <span class="info-value">{appt.get('proposed_date','—')}</span>
  </div>
  <div class="info-row">
    <span class="info-label">Horario</span>
    <span class="info-value">{appt.get('proposed_start_time','—')} – {appt.get('proposed_end_time','—')}</span>
  </div>
  {f'<div class="info-row"><span class="info-label">Motivo</span><span class="info-value">{appt["reschedule_reason"]}</span></div>' if appt.get('reschedule_reason') else ''}
</div>

<p>Ingresa a tu cuenta para <strong>aceptar o rechazar</strong> el reagendamiento.</p>
"""
    return _base_template(content)


def _html_reschedule_accepted(first_name: str, appt: dict) -> str:
    content = f"""
<h2>Reagendamiento confirmado ✅</h2>
<p>Hola <strong>{first_name}</strong>, aceptaste el reagendamiento. Tu cita ha sido actualizada
al nuevo horario:</p>
<div class="info-box">
  <span class="badge badge-confirmada">REAGENDADA</span>
  <hr class="divider" style="margin:12px 0;">
  {_appt_rows(appt)}
</div>
<p style="font-size:13px;color:#888;">Recuerda llegar con al menos 5 minutos de anticipación.</p>
"""
    return _base_template(content)


def _html_reschedule_rejected(first_name: str, appt: dict) -> str:
    content = f"""
<h2>Tu cita se mantiene en el horario original</h2>
<p>Hola <strong>{first_name}</strong>, rechazaste la propuesta de reagendamiento.
Tu cita continúa en el horario original:</p>
<div class="info-box">
  <span class="badge badge-confirmada">CONFIRMADA</span>
  <hr class="divider" style="margin:12px 0;">
  {_appt_rows(appt)}
</div>
"""
    return _base_template(content)


def _html_password_reset(first_name: str, reset_url: str) -> str:
    content = f"""
<h2>Recupera tu contraseña 🔐</h2>
<p>Hola <strong>{first_name}</strong>, recibimos una solicitud para restablecer la contraseña
de tu cuenta en <strong>Shirley Buenaño</strong>.</p>
<p>Haz clic en el botón para crear una nueva contraseña. Este enlace es válido por
<strong>1 hora</strong>.</p>
<div style="text-align:center;margin:28px 0;">
  <a href="{reset_url}" class="btn"
     style="background:{_PRIMARY};color:#fff;padding:14px 32px;border-radius:8px;
            text-decoration:none;font-weight:700;font-size:15px;">
    Restablecer Contraseña
  </a>
</div>
<p style="font-size:13px;color:#888;">Si no puedes hacer clic en el botón, copia y pega
este enlace en tu navegador:<br>
<a href="{reset_url}" style="color:{_PRIMARY};word-break:break-all;">{reset_url}</a></p>
<hr style="border:none;border-top:1px solid #ede0e8;margin:20px 0;">
<p style="font-size:12px;color:#aaa;">Si no solicitaste este cambio, ignora este correo.
Tu contraseña no será modificada.</p>
"""
    return _base_template(content)


def _html_overdue_voucher_notice(first_name: str, appt: dict) -> str:
    contact = os.getenv("SALON_PHONE", "")
    contact_line = (f'<p style="margin:8px 0;font-size:14px;">📱 <strong>{contact}</strong></p>'
                    if contact else "")
    content = f"""
<h2>Hola, {first_name} 👋</h2>
<p>Notamos que tu cita con comprobante de pago <strong>no fue procesada a tiempo</strong>
por parte de nuestro equipo. Nos disculpamos por este inconveniente.</p>
<p><strong>Tu dinero está a salvo.</strong> Tienes dos opciones y tú decides:</p>

<div class="info-box" style="border-left-color:#FFC107;">
  {_appt_rows(appt)}
</div>

<table style="width:100%;border-collapse:separate;border-spacing:0 10px;margin:20px 0;">
  <tr>
    <td style="background:#e8f5e9;border-radius:8px;padding:16px 20px;width:48%;vertical-align:top;">
      <p style="margin:0 0 6px;font-weight:700;color:#2e7d32;font-size:15px;">
        📅 Opción A — Cambiar la fecha
      </p>
      <p style="margin:0;font-size:13px;color:#555;">
        Comunícate con nosotros y agendamos tu cita en un nuevo día sin costo adicional.
        Tu pago ya está registrado.
      </p>
    </td>
    <td style="width:4%;"></td>
    <td style="background:#fff3e0;border-radius:8px;padding:16px 20px;width:48%;vertical-align:top;">
      <p style="margin:0 0 6px;font-weight:700;color:#e65100;font-size:15px;">
        💰 Opción B — Devolución del dinero
      </p>
      <p style="margin:0;font-size:13px;color:#555;">
        Si prefieres que te devolvamos el pago, comunícate con nosotros y
        lo procesamos a la brevedad.
      </p>
    </td>
  </tr>
</table>

<p>Para elegir tu opción, contáctanos por cualquiera de estos medios:</p>
{contact_line}
<p style="margin:4px 0;font-size:14px;">
  📧 Responde directamente a este correo
</p>

<hr class="divider">
<p style="font-size:13px;color:#888;">
  Lamentamos los inconvenientes. Nuestro compromiso es garantizar tu satisfacción.
</p>"""
    return _base_template(content)


# ── Servicio público ───────────────────────────────────────────────────────────

class EmailService:

    @staticmethod
    def _send(to_email: str, subject: str, html_body: str) -> None:
        user     = os.getenv("GMAIL_USER", "").strip()
        password = os.getenv("GMAIL_APP_PASSWORD", "").strip()
        if not user or not password or "@" not in user:
            return
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = f"Shirley Buenaño <{user}>"
            msg["To"]      = to_email
            msg.attach(MIMEText(html_body, "html", "utf-8"))
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as srv:
                srv.starttls()
                srv.login(user, password)
                srv.sendmail(user, to_email, msg.as_string())
        except Exception as exc:
            print(f"[EmailService] Error enviando a {to_email}: {exc}")

    @classmethod
    def _send_async(cls, to_email: str, subject: str, html_body: str) -> None:
        threading.Thread(
            target=cls._send, args=(to_email, subject, html_body), daemon=True
        ).start()

    # ── Métodos públicos ───────────────────────────────────────────────────────

    @classmethod
    def send_welcome(cls, to_email: str, first_name: str) -> None:
        cls._send_async(to_email, "¡Bienvenida a Shirley Buenaño! ✨", _html_welcome(first_name))

    @classmethod
    def send_appointment_confirmed(cls, to_email: str, first_name: str, appt: dict) -> None:
        cls._send_async(to_email, "Tu cita ha sido confirmada ✅", _html_appointment_confirmed(first_name, appt))

    @classmethod
    def send_appointment_cancelled(cls, to_email: str, first_name: str, appt: dict) -> None:
        cls._send_async(to_email, "Tu cita ha sido cancelada", _html_appointment_cancelled(first_name, appt))

    @classmethod
    def send_reschedule_proposal(cls, to_email: str, first_name: str, appt: dict) -> None:
        cls._send_async(to_email, "Propuesta de reagendamiento 📅", _html_reschedule_proposal(first_name, appt))

    @classmethod
    def send_reschedule_accepted(cls, to_email: str, first_name: str, appt: dict) -> None:
        cls._send_async(to_email, "Reagendamiento confirmado ✅", _html_reschedule_accepted(first_name, appt))

    @classmethod
    def send_reschedule_rejected(cls, to_email: str, first_name: str, appt: dict) -> None:
        cls._send_async(to_email, "Tu cita se mantiene en el horario original", _html_reschedule_rejected(first_name, appt))

    @classmethod
    def send_password_reset(cls, to_email: str, first_name: str, reset_url: str) -> None:
        cls._send_async(to_email, "Recupera tu contraseña - Shirley Buenaño 🔐", _html_password_reset(first_name, reset_url))

    @classmethod
    def send_overdue_voucher_notice(cls, to_email: str, first_name: str, appt: dict) -> None:
        cls._send_async(
            to_email,
            "Tu cita pendiente necesita tu atención — Shirley Buenaño 📋",
            _html_overdue_voucher_notice(first_name, appt)
        )
