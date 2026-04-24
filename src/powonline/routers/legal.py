"""
Legal document endpoints.

Serves publicly accessible HTML pages for:

  GET /legal/privacy-policy    — Privacy Policy (EN / FR / DE)
  GET /legal/terms-of-service  — Terms of Service (EN / FR / DE)
  GET /legal/data-retention    — Data Retention & Right to Erasure statement

Controller identity is read from the [legal] section of the application
config and can be overridden via environment variables:

  POWONLINE_SITE_NAME     → site name shown in all documents
  POWONLINE_SITE_URL      → canonical URL of the service
  POWONLINE_CONTACT_EMAIL → data-controller contact e-mail
"""

import logging

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from powonline.config import default as get_config

ROUTER = APIRouter(prefix="/legal", tags=["legal"])
LOG = logging.getLogger(__name__)

_EFFECTIVE_DATE = "April 24, 2026"


def _legal_context() -> dict:
    """Return the three configurable controller identity strings."""
    try:
        cfg = get_config()
        return {
            "site_name": cfg.get("legal", "site_name", fallback="This Service"),
            "site_url": cfg.get("legal", "site_url", fallback="#"),
            "contact_email": cfg.get(
                "legal", "contact_email", fallback="contact@example.com"
            ),
        }
    except Exception:
        LOG.warning("Could not read [legal] config; using placeholder values.")
        return {
            "site_name": "This Service",
            "site_url": "#",
            "contact_email": "contact@example.com",
        }


# ---------------------------------------------------------------------------
# Shared CSS / chrome
# ---------------------------------------------------------------------------

_CSS = """
body { font-family: sans-serif; max-width: 860px; margin: 2rem auto; padding: 0 1rem; color: #222; }
h1 { font-size: 1.8rem; margin-bottom: 0.25rem; }
h2 { font-size: 1.3rem; margin-top: 2rem; border-bottom: 1px solid #ddd; padding-bottom: 0.3rem; }
h3 { font-size: 1.1rem; margin-top: 1.5rem; }
p, li { line-height: 1.7; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
th, td { border: 1px solid #ccc; padding: 0.4rem 0.7rem; text-align: left; }
th { background: #f5f5f5; }
.lang-tabs { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }
.lang-tabs a { padding: 0.3rem 0.8rem; border: 1px solid #aaa; border-radius: 4px;
               text-decoration: none; color: #333; }
.lang-tabs a:hover { background: #eee; }
.effective { color: #666; font-size: 0.9rem; }
"""


def _html_page(title: str, body: str, lang_links: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>{title}</title>
<style>{_CSS}</style></head>
<body>
{lang_links}
{body}
</body></html>"""


# ---------------------------------------------------------------------------
# Privacy Policy
# ---------------------------------------------------------------------------


def _privacy_en(ctx: dict) -> str:
    n = ctx["site_name"]
    u = ctx["site_url"]
    e = ctx["contact_email"]
    return f"""
<h1>Privacy Policy</h1>
<p class="effective">Effective date: {_EFFECTIVE_DATE}</p>

<p>{n} (&ldquo;we&rdquo;, &ldquo;us&rdquo;, &ldquo;our&rdquo;) operates {u}
(the &ldquo;Service&rdquo;). This policy explains how we collect, use and
protect your personal data in accordance with Regulation (EU) 2016/679
(GDPR).</p>

<h2>1. Data Controller</h2>
<p>{n} &mdash; contact: <a href="mailto:{e}">{e}</a></p>

<h2>2. Personal Data We Collect</h2>
<ul>
  <li><strong>Account data:</strong> username, e-mail address (used as primary
  identifier and for account recovery).</li>
  <li><strong>OAuth connection data:</strong> provider name, provider user ID,
  display name, profile URL, avatar URL, and a short-lived access token
  when you log in via a third-party provider (Google, GitHub, Microsoft,
  Facebook, or a generic OIDC provider).</li>
  <li><strong>Uploaded files:</strong> images or other files you voluntarily
  upload during an event.</li>
  <li><strong>Audit log:</strong> timestamps and descriptions of significant
  actions (e.g. score changes) linked to your username. Username references
  are nulled when an account is deleted; the log itself is retained for
  operational integrity.</li>
</ul>
<p>We do <strong>not</strong> collect phone numbers, IP addresses, device
identifiers, or any form of analytics or tracking data.</p>

<h2>3. Cookies</h2>
<p>This Service uses <strong>strictly necessary</strong> HttpOnly cookies only.
No consent banner is displayed because no non-essential cookies are set.</p>
<table>
  <tr><th>Cookie</th><th>Purpose</th><th>Lifetime</th></tr>
  <tr><td><code>access_token</code></td>
      <td>Signed JWT authenticating your session. Read by the server on every
      request; never accessible to JavaScript.</td>
      <td>15 minutes</td></tr>
  <tr><td><code>refresh_token</code></td>
      <td>Long-lived JWT used solely to issue a new access token without
      requiring you to log in again.</td>
      <td>7 days</td></tr>
  <tr><td><code>pkce_state</code></td>
      <td>Transient PKCE state carried across the OAuth redirect round-trip.
      Deleted immediately after use.</td>
      <td>10 minutes</td></tr>
</table>
<p>You may refuse cookies by adjusting your browser settings; however, the
Service will not function without the authentication cookies above.</p>

<h2>4. Legal Basis for Processing</h2>
<ul>
  <li>Account data and cookies: <em>contract performance</em> (Art. 6(1)(b) GDPR) &mdash;
  necessary to provide the Service.</li>
  <li>Audit log: <em>legitimate interests</em> (Art. 6(1)(f) GDPR) &mdash;
  operational integrity and fraud prevention.</li>
</ul>

<h2>5. Social Login &amp; Third-Party Providers</h2>
<p>If you log in via Google, GitHub, Microsoft, Facebook, or an OIDC provider,
your browser is redirected to that provider. The provider&rsquo;s own privacy
policy governs data exchanged during that redirect. We receive only the minimal
profile information needed to create or match your account (e-mail, display
name, provider user ID).</p>

<h2>6. Data Retention</h2>
<p>We retain personal data only as long as necessary for the purposes described
above. Account data is retained until you delete your account. Audit log
entries are retained indefinitely in anonymised form (username is nulled on
account deletion) for operational integrity.</p>

<h2>7. Your GDPR Rights</h2>
<ul>
  <li><strong>Access &amp; portability:</strong> you may request a copy of your
  data by contacting us.</li>
  <li><strong>Rectification:</strong> contact us to correct inaccurate
  data.</li>
  <li><strong>Erasure (right to be forgotten):</strong> you can permanently
  delete your account and all associated personal data at any time from the
  <a href="/account">Account Settings</a> page. Alternatively, contact us at
  <a href="mailto:{e}">{e}</a>.</li>
  <li><strong>Restriction &amp; objection:</strong> you may ask us to restrict
  processing or object to it by contacting us.</li>
  <li><strong>Withdraw consent:</strong> where processing is based on consent,
  you may withdraw it at any time.</li>
  <li><strong>Lodge a complaint:</strong> you have the right to complain to the
  <em>Commission Nationale pour la Protection des Données</em> (CNPD),
  Luxembourg&rsquo;s supervisory authority, or the authority of your
  country of residence.</li>
</ul>

<h2>8. Children</h2>
<p>The Service is not directed at persons under 18. We do not knowingly collect
data from children. If you believe a child has provided data, contact us and
we will delete it.</p>

<h2>9. Changes to This Policy</h2>
<p>We may update this policy. The effective date at the top will be updated and
we will notify users of material changes via the Service.</p>

<h2>10. Contact</h2>
<p>Data Controller: {n} &mdash; <a href="mailto:{e}">{e}</a></p>
"""


def _privacy_fr(ctx: dict) -> str:
    n = ctx["site_name"]
    u = ctx["site_url"]
    e = ctx["contact_email"]
    return f"""
<h1>Politique de Confidentialité</h1>
<p class="effective">Date de prise d'effet&nbsp;: {_EFFECTIVE_DATE}</p>

<p>{n} («&nbsp;nous&nbsp;») exploite {u} (le «&nbsp;Service&nbsp;»). La
présente politique explique comment nous collectons, utilisons et protégeons vos
données personnelles conformément au Règlement (UE) 2016/679 (RGPD).</p>

<h2>1. Responsable du traitement</h2>
<p>{n} &mdash; contact&nbsp;: <a href="mailto:{e}">{e}</a></p>

<h2>2. Données personnelles collectées</h2>
<ul>
  <li><strong>Données de compte&nbsp;:</strong> nom d'utilisateur, adresse
  e-mail (identifiant principal et récupération de compte).</li>
  <li><strong>Données de connexion OAuth&nbsp;:</strong> nom du fournisseur,
  identifiant utilisateur chez le fournisseur, nom d'affichage, URL de profil,
  URL d'avatar et jeton d'accès de courte durée lors d'une connexion via un
  fournisseur tiers (Google, GitHub, Microsoft, Facebook ou OIDC générique).</li>
  <li><strong>Fichiers téléversés&nbsp;:</strong> images ou autres fichiers que
  vous déposez volontairement lors d'un événement.</li>
  <li><strong>Journal d'audit&nbsp;:</strong> horodatages et descriptions
  d'actions significatives liés à votre nom d'utilisateur. Ce champ est mis à
  NULL lors de la suppression du compte ; le journal est conservé pour
  l'intégrité opérationnelle.</li>
</ul>
<p>Nous ne collectons <strong>pas</strong> de numéros de téléphone, adresses IP,
identifiants de dispositifs ni aucune donnée d'analyse ou de traçage.</p>

<h2>3. Cookies</h2>
<p>Ce Service utilise uniquement des cookies <strong>strictement
nécessaires</strong> de type HttpOnly. Aucune bannière de consentement
n'est affichée car aucun cookie non essentiel n'est posé.</p>
<table>
  <tr><th>Cookie</th><th>Finalité</th><th>Durée</th></tr>
  <tr><td><code>access_token</code></td>
      <td>JWT signé authentifiant votre session. Lu par le serveur à chaque
      requête ; jamais accessible au JavaScript.</td>
      <td>15 minutes</td></tr>
  <tr><td><code>refresh_token</code></td>
      <td>JWT longue durée utilisé uniquement pour émettre un nouveau jeton
      d'accès sans reconnexion.</td>
      <td>7 jours</td></tr>
  <tr><td><code>pkce_state</code></td>
      <td>État PKCE transitoire transmis lors de la redirection OAuth.
      Supprimé immédiatement après utilisation.</td>
      <td>10 minutes</td></tr>
</table>
<p>Vous pouvez refuser les cookies via les paramètres de votre navigateur,
mais le Service ne fonctionnera pas sans les cookies d'authentification
ci-dessus.</p>

<h2>4. Base juridique du traitement</h2>
<ul>
  <li>Données de compte et cookies&nbsp;: <em>exécution d'un contrat</em>
  (Art. 6(1)(b) RGPD) &mdash; nécessaire à la fourniture du Service.</li>
  <li>Journal d'audit&nbsp;: <em>intérêts légitimes</em> (Art. 6(1)(f) RGPD)
  &mdash; intégrité opérationnelle et prévention des fraudes.</li>
</ul>

<h2>5. Connexion sociale et fournisseurs tiers</h2>
<p>Si vous vous connectez via Google, GitHub, Microsoft, Facebook ou un
fournisseur OIDC, votre navigateur est redirigé vers ce fournisseur. La
politique de confidentialité de ce fournisseur s'applique à cet échange. Nous
recevons uniquement les informations de profil minimales nécessaires pour créer
ou identifier votre compte (e-mail, nom d'affichage, identifiant fournisseur).</p>

<h2>6. Conservation des données</h2>
<p>Nous conservons les données personnelles uniquement le temps nécessaire aux
finalités décrites. Les données de compte sont conservées jusqu'à la suppression
de votre compte. Les entrées du journal d'audit sont conservées indéfiniment sous
forme anonymisée.</p>

<h2>7. Vos droits RGPD</h2>
<ul>
  <li><strong>Accès et portabilité&nbsp;:</strong> contactez-nous pour obtenir
  une copie de vos données.</li>
  <li><strong>Rectification&nbsp;:</strong> contactez-nous pour corriger des
  données inexactes.</li>
  <li><strong>Effacement (droit à l'oubli)&nbsp;:</strong> vous pouvez supprimer
  définitivement votre compte depuis la page
  <a href="/account">Paramètres du compte</a>. Vous pouvez également nous
  contacter à <a href="mailto:{e}">{e}</a>.</li>
  <li><strong>Limitation et opposition&nbsp;:</strong> contactez-nous pour
  demander la limitation du traitement ou vous y opposer.</li>
  <li><strong>Retrait du consentement&nbsp;:</strong> lorsque le traitement est
  fondé sur le consentement, vous pouvez le retirer à tout moment.</li>
  <li><strong>Réclamation&nbsp;:</strong> vous pouvez déposer une plainte auprès
  de la <em>Commission Nationale pour la Protection des Données</em> (CNPD) ou
  de l'autorité de contrôle de votre pays de résidence.</li>
</ul>

<h2>8. Enfants</h2>
<p>Le Service n'est pas destiné aux personnes de moins de 18 ans. Si vous pensez
qu'un enfant nous a fourni des données, contactez-nous.</p>

<h2>9. Modifications</h2>
<p>Nous pouvons mettre à jour cette politique. La date d'effet sera actualisée et
les modifications substantielles seront notifiées aux utilisateurs.</p>

<h2>10. Contact</h2>
<p>Responsable du traitement&nbsp;: {n} &mdash;
<a href="mailto:{e}">{e}</a></p>
"""


def _privacy_de(ctx: dict) -> str:
    n = ctx["site_name"]
    u = ctx["site_url"]
    e = ctx["contact_email"]
    return f"""
<h1>Datenschutzerklärung</h1>
<p class="effective">Datum des Inkrafttretens: {_EFFECTIVE_DATE}</p>

<p>{n} («wir», «uns», «unser») betreibt {u} (den «Dienst»). Diese Erklärung
beschreibt, wie wir Ihre personenbezogenen Daten gemäß der Verordnung (EU)
2016/679 (DSGVO) erheben, verwenden und schützen.</p>

<h2>1. Verantwortlicher</h2>
<p>{n} &mdash; Kontakt: <a href="mailto:{e}">{e}</a></p>

<h2>2. Erhobene personenbezogene Daten</h2>
<ul>
  <li><strong>Kontodaten:</strong> Benutzername, E-Mail-Adresse (als
  Hauptidentifikator und zur Kontowiederherstellung).</li>
  <li><strong>OAuth-Verbindungsdaten:</strong> Anbietername, Benutzer-ID beim
  Anbieter, Anzeigename, Profil-URL, Avatar-URL sowie kurzlebiges Zugriffstoken
  bei Anmeldung über einen Drittanbieter (Google, GitHub, Microsoft, Facebook
  oder generischer OIDC-Anbieter).</li>
  <li><strong>Hochgeladene Dateien:</strong> Bilder oder andere Dateien, die Sie
  während einer Veranstaltung freiwillig hochladen.</li>
  <li><strong>Audit-Log:</strong> Zeitstempel und Beschreibungen wesentlicher
  Aktionen, verknüpft mit Ihrem Benutzernamen. Der Benutzername wird bei
  Kontolöschung auf NULL gesetzt; der Log bleibt aus betrieblichen Gründen
  erhalten.</li>
</ul>
<p>Wir erheben <strong>keine</strong> Telefonnummern, IP-Adressen,
Gerätekennungen oder Analyse- und Tracking-Daten.</p>

<h2>3. Cookies</h2>
<p>Dieser Dienst verwendet ausschließlich <strong>technisch notwendige</strong>
HttpOnly-Cookies. Da keine nicht notwendigen Cookies gesetzt werden, wird kein
Cookie-Einwilligungsbanner angezeigt.</p>
<table>
  <tr><th>Cookie</th><th>Zweck</th><th>Lebensdauer</th></tr>
  <tr><td><code>access_token</code></td>
      <td>Signiertes JWT zur Sitzungsauthentifizierung. Wird vom Server bei
      jeder Anfrage gelesen; für JavaScript nicht zugänglich.</td>
      <td>15 Minuten</td></tr>
  <tr><td><code>refresh_token</code></td>
      <td>Langlebiges JWT, das ausschließlich dazu dient, ein neues
      Zugriffstoken ohne erneute Anmeldung auszustellen.</td>
      <td>7 Tage</td></tr>
  <tr><td><code>pkce_state</code></td>
      <td>Transienter PKCE-Zustand für den OAuth-Redirect. Wird unmittelbar nach
      Verwendung gelöscht.</td>
      <td>10 Minuten</td></tr>
</table>
<p>Sie können Cookies über Ihre Browsereinstellungen ablehnen; der Dienst
funktioniert jedoch ohne die oben genannten Authentifizierungs-Cookies
nicht.</p>

<h2>4. Rechtsgrundlage der Verarbeitung</h2>
<ul>
  <li>Kontodaten und Cookies: <em>Vertragserfüllung</em> (Art. 6 Abs. 1 lit. b
  DSGVO) &mdash; zur Erbringung des Dienstes erforderlich.</li>
  <li>Audit-Log: <em>berechtigte Interessen</em> (Art. 6 Abs. 1 lit. f DSGVO)
  &mdash; Betriebsintegrität und Betrugsvorbeugung.</li>
</ul>

<h2>5. Social-Login und Drittanbieter</h2>
<p>Bei Anmeldung über Google, GitHub, Microsoft, Facebook oder einen
OIDC-Anbieter wird Ihr Browser zu diesem Anbieter weitergeleitet. Für den
dabei stattfindenden Datenaustausch gilt die Datenschutzerklärung des
jeweiligen Anbieters. Wir erhalten nur die minimalen Profilinformationen, die
zum Erstellen oder Abgleichen Ihres Kontos erforderlich sind (E-Mail,
Anzeigename, Anbieter-Benutzer-ID).</p>

<h2>6. Aufbewahrung von Daten</h2>
<p>Wir speichern personenbezogene Daten nur so lange, wie es für die genannten
Zwecke erforderlich ist. Kontodaten werden bis zur Löschung Ihres Kontos
gespeichert. Audit-Log-Einträge werden dauerhaft in anonymisierter Form
aufbewahrt.</p>

<h2>7. Ihre Rechte nach der DSGVO</h2>
<ul>
  <li><strong>Auskunft und Portabilität:</strong> Sie können eine Kopie Ihrer
  Daten anfordern.</li>
  <li><strong>Berichtigung:</strong> Kontaktieren Sie uns, um unrichtige Daten
  zu korrigieren.</li>
  <li><strong>Löschung (Recht auf Vergessenwerden):</strong> Sie können Ihr
  Konto und alle damit verbundenen personenbezogenen Daten jederzeit über die
  <a href="/account">Kontoeinstellungen</a> dauerhaft löschen. Alternativ
  wenden Sie sich an <a href="mailto:{e}">{e}</a>.</li>
  <li><strong>Einschränkung und Widerspruch:</strong> Sie können die
  Einschränkung der Verarbeitung verlangen oder ihr widersprechen.</li>
  <li><strong>Widerruf der Einwilligung:</strong> Soweit die Verarbeitung auf
  Ihrer Einwilligung beruht, können Sie diese jederzeit widerrufen.</li>
  <li><strong>Beschwerde:</strong> Sie können eine Beschwerde bei der
  <em>Commission Nationale pour la Protection des Données</em> (CNPD),
  Luxemburgs Datenschutzbehörde, oder der Aufsichtsbehörde Ihres Wohnsitzlandes
  einreichen.</li>
</ul>

<h2>8. Kinder</h2>
<p>Der Dienst richtet sich nicht an Personen unter 18 Jahren. Falls Sie der
Meinung sind, dass ein Kind uns Daten übermittelt hat, kontaktieren Sie
uns bitte.</p>

<h2>9. Änderungen</h2>
<p>Wir können diese Erklärung aktualisieren. Das Datum des Inkrafttretens wird
dann geändert; wesentliche Änderungen werden den Nutzern über den Dienst
mitgeteilt.</p>

<h2>10. Kontakt</h2>
<p>Verantwortlicher: {n} &mdash; <a href="mailto:{e}">{e}</a></p>
"""


@ROUTER.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_policy(lang: str = "en") -> HTMLResponse:
    """Public privacy policy in English, French, or German."""
    ctx = _legal_context()
    n = ctx["site_name"]
    lang_links = (
        '<div class="lang-tabs">'
        '<a href="?lang=en">EN</a>'
        '<a href="?lang=fr">FR</a>'
        '<a href="?lang=de">DE</a>'
        "</div>"
    )
    if lang == "fr":
        body = _privacy_fr(ctx)
        title = f"Politique de Confidentialité — {n}"
    elif lang == "de":
        body = _privacy_de(ctx)
        title = f"Datenschutzerklärung — {n}"
    else:
        body = _privacy_en(ctx)
        title = f"Privacy Policy — {n}"
    return HTMLResponse(_html_page(title, body, lang_links))


# ---------------------------------------------------------------------------
# Terms of Service
# ---------------------------------------------------------------------------


def _tos_en(ctx: dict) -> str:
    n = ctx["site_name"]
    u = ctx["site_url"]
    e = ctx["contact_email"]
    return f"""
<h1>Terms of Service</h1>
<p class="effective">Effective date: {_EFFECTIVE_DATE}</p>

<p>Please read these Terms of Service (&ldquo;Terms&rdquo;) carefully before
using {u} operated by {n} (&ldquo;we&rdquo;, &ldquo;us&rdquo;,
&ldquo;our&rdquo;).</p>

<h2>1. Acceptance of Terms</h2>
<p>By accessing or using the Service you agree to be bound by these Terms and
our <a href="/legal/privacy-policy">Privacy Policy</a>. If you do not agree,
do not use the Service.</p>

<h2>2. Description of Service</h2>
<p>The Service is an event-management and real-time team-tracking platform for
organised outdoor events. It enables event organisers to manage teams, routes,
stations, scores, and uploads.</p>

<h2>3. Accounts</h2>
<ul>
  <li>You are responsible for maintaining the confidentiality of your account
  credentials.</li>
  <li>You must provide accurate information when registering.</li>
  <li>You must be at least 18 years old to create an account.</li>
  <li>You are responsible for all activity that occurs under your account.</li>
  <li>Notify us immediately at <a href="mailto:{e}">{e}</a> if you suspect
  unauthorised use of your account.</li>
</ul>

<h2>4. Permitted Use</h2>
<p>You may use the Service only for lawful purposes and in accordance with these
Terms. You agree not to:</p>
<ul>
  <li>Upload content that is unlawful, harmful, threatening, abusive, defamatory,
  obscene, or otherwise objectionable.</li>
  <li>Impersonate any person or entity or misrepresent your affiliation.</li>
  <li>Interfere with or disrupt the Service or servers.</li>
  <li>Attempt to gain unauthorised access to any portion of the Service.</li>
  <li>Use automated means to scrape or harvest data without our written
  consent.</li>
</ul>

<h2>5. User Content</h2>
<p>You retain ownership of content you upload. By uploading content you grant
us a non-exclusive, royalty-free licence to store and display it solely for the
purpose of operating the Service. You represent that you have all necessary
rights to the content you upload.</p>

<h2>6. Account Deletion</h2>
<p>You may delete your account at any time from the
<a href="/account">Account Settings</a> page or by contacting us at
<a href="mailto:{e}">{e}</a>. Upon deletion, your personal data is erased in
accordance with our <a href="/legal/privacy-policy">Privacy Policy</a> and
<a href="/legal/data-retention">Data Retention Statement</a>.</p>

<h2>7. Service Availability</h2>
<p>We provide the Service on an &ldquo;as is&rdquo; and &ldquo;as
available&rdquo; basis. We do not guarantee uninterrupted or error-free
operation. We reserve the right to modify, suspend, or discontinue the Service
at any time with reasonable notice.</p>

<h2>8. Limitation of Liability</h2>
<p>To the maximum extent permitted by applicable law, {n} shall not be liable
for any indirect, incidental, special, consequential, or punitive damages
arising from your use of or inability to use the Service. Our total liability
for any claim shall not exceed the amount you paid us in the twelve months
preceding the claim (or €50 if no payment was made).</p>

<h2>9. Third-Party Services</h2>
<p>The Service may integrate with third-party identity providers (Google,
GitHub, Microsoft, Facebook, OIDC). Your use of those services is subject to
their respective terms and privacy policies. We are not responsible for
third-party services.</p>

<h2>10. Governing Law</h2>
<p>These Terms are governed by the laws of the Grand Duchy of Luxembourg.
Any dispute shall be subject to the exclusive jurisdiction of the courts of
Luxembourg City, unless mandatory consumer protection rules in your country
of residence require otherwise.</p>

<h2>11. Changes to These Terms</h2>
<p>We may update these Terms. We will notify you of material changes via the
Service. Continued use after changes are posted constitutes acceptance.</p>

<h2>12. Contact</h2>
<p>{n} &mdash; <a href="mailto:{e}">{e}</a></p>
"""


def _tos_fr(ctx: dict) -> str:
    n = ctx["site_name"]
    u = ctx["site_url"]
    e = ctx["contact_email"]
    return f"""
<h1>Conditions Générales d'Utilisation</h1>
<p class="effective">Date de prise d'effet&nbsp;: {_EFFECTIVE_DATE}</p>

<p>Veuillez lire attentivement les présentes Conditions Générales
(«&nbsp;Conditions&nbsp;») avant d'utiliser {u} exploité par {n}
(«&nbsp;nous&nbsp;»).</p>

<h2>1. Acceptation des Conditions</h2>
<p>En accédant au Service ou en l'utilisant, vous acceptez d'être lié par les
présentes Conditions et notre
<a href="/legal/privacy-policy?lang=fr">Politique de Confidentialité</a>. Si
vous n'acceptez pas ces Conditions, n'utilisez pas le Service.</p>

<h2>2. Description du Service</h2>
<p>Le Service est une plateforme de gestion d'événements et de suivi en temps
réel d'équipes lors d'événements de plein air organisés.</p>

<h2>3. Comptes</h2>
<ul>
  <li>Vous êtes responsable de la confidentialité de vos identifiants.</li>
  <li>Vous devez fournir des informations exactes lors de l'inscription.</li>
  <li>Vous devez avoir au moins 18 ans pour créer un compte.</li>
  <li>Signalez toute utilisation non autorisée à
  <a href="mailto:{e}">{e}</a>.</li>
</ul>

<h2>4. Utilisation autorisée</h2>
<p>Vous vous engagez à ne pas&nbsp;:</p>
<ul>
  <li>Téléverser des contenus illicites, nuisibles, diffamatoires ou
  répréhensibles.</li>
  <li>Usurper l'identité d'une personne ou d'une entité.</li>
  <li>Perturber ou interférer avec le Service.</li>
  <li>Tenter d'accéder sans autorisation à des parties du Service.</li>
  <li>Utiliser des moyens automatisés pour extraire des données sans notre
  consentement écrit.</li>
</ul>

<h2>5. Contenu utilisateur</h2>
<p>Vous conservez la propriété des contenus que vous téléversez. En les
téléversant, vous nous accordez une licence non exclusive et sans redevance
pour les stocker et les afficher aux seules fins du Service.</p>

<h2>6. Suppression de compte</h2>
<p>Vous pouvez supprimer votre compte à tout moment depuis la page
<a href="/account">Paramètres du compte</a> ou en nous contactant à
<a href="mailto:{e}">{e}</a>.</p>

<h2>7. Disponibilité du Service</h2>
<p>Le Service est fourni «&nbsp;tel quel&nbsp;». Nous nous réservons le droit
de le modifier, de le suspendre ou d'y mettre fin avec un préavis raisonnable.</p>

<h2>8. Limitation de responsabilité</h2>
<p>Dans la limite autorisée par la loi applicable, {n} ne saurait être tenu
responsable de dommages indirects, accessoires, spéciaux ou consécutifs
résultant de l'utilisation du Service.</p>

<h2>9. Loi applicable</h2>
<p>Les présentes Conditions sont régies par le droit du Grand-Duché de
Luxembourg. Tout litige relève de la compétence exclusive des tribunaux de
Luxembourg-Ville, sauf dispositions impératives contraires applicables dans
votre pays de résidence.</p>

<h2>10. Modifications</h2>
<p>Nous pouvons mettre à jour ces Conditions. L'utilisation continue après
la publication des modifications vaut acceptation.</p>

<h2>11. Contact</h2>
<p>{n} &mdash; <a href="mailto:{e}">{e}</a></p>
"""


def _tos_de(ctx: dict) -> str:
    n = ctx["site_name"]
    u = ctx["site_url"]
    e = ctx["contact_email"]
    return f"""
<h1>Nutzungsbedingungen</h1>
<p class="effective">Datum des Inkrafttretens: {_EFFECTIVE_DATE}</p>

<p>Bitte lesen Sie diese Nutzungsbedingungen («Bedingungen») sorgfältig, bevor
Sie {u} von {n} («wir», «uns», «unser») nutzen.</p>

<h2>1. Annahme der Bedingungen</h2>
<p>Durch den Zugriff auf den Dienst oder seine Nutzung erklären Sie sich mit
diesen Bedingungen und unserer
<a href="/legal/privacy-policy?lang=de">Datenschutzerklärung</a>
einverstanden.</p>

<h2>2. Beschreibung des Dienstes</h2>
<p>Der Dienst ist eine Veranstaltungsmanagement- und Echtzeit-Tracking-Plattform
für organisierte Outdoor-Veranstaltungen.</p>

<h2>3. Konten</h2>
<ul>
  <li>Sie sind für die Vertraulichkeit Ihrer Zugangsdaten verantwortlich.</li>
  <li>Sie müssen bei der Registrierung genaue Angaben machen.</li>
  <li>Sie müssen mindestens 18 Jahre alt sein, um ein Konto zu erstellen.</li>
  <li>Melden Sie unbefugte Nutzung umgehend an
  <a href="mailto:{e}">{e}</a>.</li>
</ul>

<h2>4. Zulässige Nutzung</h2>
<p>Sie verpflichten sich, Folgendes zu unterlassen:</p>
<ul>
  <li>Hochladen rechtswidriger, schädlicher, diffamierender oder anstößiger
  Inhalte.</li>
  <li>Identitätsbetrug oder falsche Darstellung Ihrer Zugehörigkeit.</li>
  <li>Störung des Dienstes oder der Server.</li>
  <li>Versuchter unbefugter Zugriff auf Teile des Dienstes.</li>
  <li>Nutzung automatisierter Mittel zur Datenerfassung ohne unsere schriftliche
  Zustimmung.</li>
</ul>

<h2>5. Nutzerinhalte</h2>
<p>Sie behalten das Eigentum an hochgeladenen Inhalten. Durch das Hochladen
räumen Sie uns eine nicht exklusive, gebührenfreie Lizenz zur Speicherung und
Anzeige ausschließlich zum Betrieb des Dienstes ein.</p>

<h2>6. Kontolöschung</h2>
<p>Sie können Ihr Konto jederzeit über die
<a href="/account">Kontoeinstellungen</a> oder per Kontakt an
<a href="mailto:{e}">{e}</a> löschen.</p>

<h2>7. Dienstverfügbarkeit</h2>
<p>Der Dienst wird «wie besehen» bereitgestellt. Wir behalten uns das Recht
vor, den Dienst mit angemessener Vorankündigung zu ändern, auszusetzen oder
einzustellen.</p>

<h2>8. Haftungsbeschränkung</h2>
<p>Im gesetzlich zulässigen Rahmen haftet {n} nicht für indirekte, zufällige,
besondere oder Folgeschäden aus der Nutzung des Dienstes.</p>

<h2>9. Anwendbares Recht</h2>
<p>Diese Bedingungen unterliegen dem Recht des Großherzogtums Luxemburg. Für
Streitigkeiten sind die Gerichte der Stadt Luxemburg ausschließlich zuständig,
sofern keine zwingenden Verbraucherschutzvorschriften Ihres Wohnsitzlandes
entgegenstehen.</p>

<h2>10. Änderungen</h2>
<p>Wir können diese Bedingungen aktualisieren. Die weitere Nutzung nach
Veröffentlichung der Änderungen gilt als Zustimmung.</p>

<h2>11. Kontakt</h2>
<p>{n} &mdash; <a href="mailto:{e}">{e}</a></p>
"""


@ROUTER.get("/terms-of-service", response_class=HTMLResponse)
async def terms_of_service(lang: str = "en") -> HTMLResponse:
    """Public Terms of Service in English, French, or German."""
    ctx = _legal_context()
    n = ctx["site_name"]
    lang_links = (
        '<div class="lang-tabs">'
        '<a href="?lang=en">EN</a>'
        '<a href="?lang=fr">FR</a>'
        '<a href="?lang=de">DE</a>'
        "</div>"
    )
    if lang == "fr":
        body = _tos_fr(ctx)
        title = f"Conditions Générales d'Utilisation — {n}"
    elif lang == "de":
        body = _tos_de(ctx)
        title = f"Nutzungsbedingungen — {n}"
    else:
        body = _tos_en(ctx)
        title = f"Terms of Service — {n}"
    return HTMLResponse(_html_page(title, body, lang_links))


# ---------------------------------------------------------------------------
# Data Retention Statement
# ---------------------------------------------------------------------------


@ROUTER.get("/data-retention", response_class=HTMLResponse)
async def data_retention() -> HTMLResponse:
    """Data retention and right-to-erasure statement."""
    ctx = _legal_context()
    n = ctx["site_name"]
    e = ctx["contact_email"]
    body = f"""
<h1>Data Retention &amp; Right to Erasure</h1>
<p class="effective">Effective date: {_EFFECTIVE_DATE}</p>
<p>This statement describes how long {n} retains each category of personal data
and how you can exercise your right to erasure (GDPR Art. 17).</p>

<h2>Data Categories and Retention Periods</h2>
<table>
  <tr>
    <th>Data Category</th>
    <th>Stored Where</th>
    <th>Retention Period</th>
    <th>On Account Deletion</th>
  </tr>
  <tr>
    <td>Username &amp; e-mail address</td>
    <td>Server database (<code>user</code> table)</td>
    <td>Until account is deleted</td>
    <td>Permanently erased</td>
  </tr>
  <tr>
    <td>Hashed password</td>
    <td>Server database (<code>user</code> table)</td>
    <td>Until account is deleted</td>
    <td>Permanently erased</td>
  </tr>
  <tr>
    <td>OAuth connection data (provider ID, access token, avatar URL)</td>
    <td>Server database (<code>oauth_connection</code> table)</td>
    <td>Until account is deleted or provider is unlinked</td>
    <td>Permanently erased (CASCADE)</td>
  </tr>
  <tr>
    <td>Role and event membership assignments</td>
    <td>Server database (<code>user_role</code>, <code>event_user_role</code>,
    <code>user_station</code> tables)</td>
    <td>Until account is deleted</td>
    <td>Permanently erased (CASCADE)</td>
  </tr>
  <tr>
    <td>Uploaded files</td>
    <td>Server database &amp; file storage</td>
    <td>Until file is deleted or account is deleted</td>
    <td>Permanently erased (CASCADE)</td>
  </tr>
  <tr>
    <td>Audit log entries (action type, timestamp, message)</td>
    <td>Server database (<code>auditlog</code> table)</td>
    <td>Indefinitely (anonymised on account deletion)</td>
    <td>Username field set to NULL; log entry retained for operational
    integrity</td>
  </tr>
  <tr>
    <td>Team ownership</td>
    <td>Server database (<code>team</code> table)</td>
    <td>Until event data is purged</td>
    <td>Ownership transferred to anonymous sentinel &mdash; team history
    preserved for other participants</td>
  </tr>
  <tr>
    <td>Authentication cookies (<code>access_token</code>,
    <code>refresh_token</code>, <code>pkce_state</code>)</td>
    <td>Browser (HttpOnly cookies, never accessible to JavaScript)</td>
    <td>15 min / 7 days / 10 min respectively</td>
    <td>Cleared immediately on logout or account deletion</td>
  </tr>
</table>

<h2>How to Request Erasure</h2>
<p>You can delete your account and all associated personal data at any time:</p>
<ul>
  <li><strong>Self-service:</strong> log in and navigate to
  <a href="/account">Account Settings</a>, then use the
  &ldquo;Delete my account&rdquo; section.</li>
  <li><strong>By e-mail:</strong> send a request to
  <a href="mailto:{e}">{e}</a>. We will process your request within 30 days as
  required by GDPR Art. 12(3).</li>
</ul>

<h2>Contact</h2>
<p>{n} &mdash; <a href="mailto:{e}">{e}</a></p>
"""
    return HTMLResponse(_html_page(f"Data Retention — {n}", body))
