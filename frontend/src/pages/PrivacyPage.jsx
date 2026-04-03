export default function PrivacyPage() {
  return (
    <div style={{
      minHeight: '100vh',
      background: '#07133a',
      color: '#e6edf3',
      fontFamily: "'Inter','Segoe UI',sans-serif",
      padding: '60px 24px',
    }}>
      <div style={{ maxWidth: 720, margin: '0 auto' }}>

        {/* Header */}
        <div style={{ marginBottom: 48 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
            <div style={{ width: 40, height: 40, borderRadius: 10, background: 'rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20 }}>
              ✉
            </div>
            <span style={{ fontSize: 18, fontWeight: 700, color: '#fff' }}>Claim360</span>
          </div>
          <h1 style={{ fontSize: 32, fontWeight: 700, color: '#fff', marginBottom: 8 }}>Privacy Policy</h1>
          <p style={{ color: '#8b949e', fontSize: 14 }}>
            Last updated: April 2026 &nbsp;·&nbsp; Effective immediately
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 36 }}>

          <Section title="1. Overview">
            <p>
              Claim360 ("we", "our", or "us") is an internal email campaign management tool operated by
              360 Degrees Management (CIN: U74999DL2016PTC303092). This Privacy Policy explains how we collect,
              use, and protect information when you use our platform at <a href="https://claim360.in" style={{ color: '#a8c8f0' }}>claim360.in</a>.
            </p>
          </Section>

          <Section title="2. Information We Collect">
            <ul>
              <li><strong>Account information:</strong> Your name and email address when you register.</li>
              <li><strong>Google OAuth tokens:</strong> When you connect your Gmail account, we store encrypted OAuth access and refresh tokens. We never store your Google password.</li>
              <li><strong>Gmail email address:</strong> The Gmail address linked to your connected account, used as the sender address for campaigns.</li>
              <li><strong>Email campaign data:</strong> Contact lists, email templates, and campaign send history that you upload or create.</li>
              <li><strong>Email tracking data:</strong> Open tracking data (pixel-based) to show delivery and open statistics for campaigns you send.</li>
            </ul>
          </Section>

          <Section title="3. How We Use Your Information">
            <ul>
              <li>To authenticate you and manage your account.</li>
              <li>To send email campaigns on your behalf using your connected Gmail account via the Gmail API.</li>
              <li>To display campaign statistics and delivery tracking within the platform.</li>
              <li>We do <strong>not</strong> sell, share, or transfer your data to any third parties.</li>
              <li>We do <strong>not</strong> use your data for advertising or marketing purposes.</li>
            </ul>
          </Section>

          <Section title="4. Google API Usage">
            <p>
              Claim360 uses the Gmail API to send emails on your behalf. Our use of data received from
              Google APIs adheres to the{' '}
              <a href="https://developers.google.com/terms/api-services-user-data-policy" style={{ color: '#a8c8f0' }} target="_blank" rel="noreferrer">
                Google API Services User Data Policy
              </a>
              , including the Limited Use requirements.
            </p>
            <ul>
              <li>We only request the Gmail scope necessary to send emails (<code style={{ background: 'rgba(255,255,255,0.08)', padding: '1px 6px', borderRadius: 4, fontSize: 12 }}>gmail.send</code>).</li>
              <li>We do not read, index, or store the contents of your Gmail inbox.</li>
              <li>OAuth tokens are stored securely and used only to send emails you explicitly initiate.</li>
              <li>You can revoke access at any time from the Configuration page or from your Google Account settings.</li>
            </ul>
          </Section>

          <Section title="5. Data Storage & Security">
            <ul>
              <li>All data is stored on secured servers. OAuth tokens are stored encrypted.</li>
              <li>We use HTTPS for all data transmission.</li>
              <li>Access to the platform is protected by password authentication with bcrypt hashing.</li>
              <li>Only authorised employees of 360 Degrees Management have access to production systems.</li>
            </ul>
          </Section>

          <Section title="6. Data Retention">
            <p>
              Your data is retained for as long as your account is active. You may request deletion of your
              account and all associated data by contacting us at the email below. OAuth tokens are
              immediately invalidated when you disconnect Gmail from the Configuration page.
            </p>
          </Section>

          <Section title="7. Your Rights">
            <ul>
              <li><strong>Access:</strong> You can view all data associated with your account within the platform.</li>
              <li><strong>Deletion:</strong> You can request full account and data deletion at any time.</li>
              <li><strong>Revoke OAuth:</strong> Disconnect Gmail at any time from the Configuration page or via <a href="https://myaccount.google.com/permissions" style={{ color: '#a8c8f0' }} target="_blank" rel="noreferrer">Google Account Permissions</a>.</li>
            </ul>
          </Section>

          <Section title="8. Contact Us">
            <p>
              For privacy-related questions or data deletion requests, contact us at:
            </p>
            <p style={{ marginTop: 8 }}>
              <strong>360 Degrees Management</strong><br />
              Email: <a href="mailto:info@claim360.in" style={{ color: '#a8c8f0' }}>info@claim360.in</a><br />
              Website: <a href="https://claim360.in" style={{ color: '#a8c8f0' }}>https://claim360.in</a>
            </p>
          </Section>

        </div>

        <div style={{ marginTop: 60, paddingTop: 24, borderTop: '1px solid rgba(255,255,255,0.1)', color: '#484f58', fontSize: 12, textAlign: 'center' }}>
          © 2026 360 Degrees Management · CIN: U74999DL2016PTC303092 ·{' '}
          <a href="/" style={{ color: '#484f58' }}>Back to App</a>
        </div>
      </div>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div>
      <h2 style={{ fontSize: 18, fontWeight: 600, color: '#fff', marginBottom: 12, paddingBottom: 8, borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        {title}
      </h2>
      <div style={{ color: '#b0c4de', fontSize: 14, lineHeight: 1.8, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {children}
      </div>
    </div>
  )
}
