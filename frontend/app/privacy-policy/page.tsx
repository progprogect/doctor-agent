/** Privacy Policy page for Elemental Clinic. */

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">
          Privacy Policy – Elemental Clinic
        </h1>

        <div className="prose prose-lg max-w-none">
          <p className="text-gray-700 mb-6">
            This Privacy Policy explains how Elemental Clinic ("we", "our", "us") collects, uses, and protects personal data obtained through our Instagram account and related interactions.
          </p>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              1. Information We Collect
            </h2>
            <p className="text-gray-700 mb-4">
              We may collect the following information from Instagram:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Username and public profile information</li>
              <li>Messages sent to us via direct messages or comments</li>
              <li>Contact details voluntarily provided (such as email or phone number)</li>
              <li>Any information you choose to share with us through Instagram forms or messages</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              2. How We Use the Information
            </h2>
            <p className="text-gray-700 mb-4">
              The information collected is used for the following purposes:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Responding to inquiries and messages</li>
              <li>Providing information about our services</li>
              <li>Scheduling appointments or consultations upon request</li>
              <li>Improving our communication and services</li>
              <li>Marketing and informational purposes related to our clinic</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              3. Legal Basis for Processing
            </h2>
            <p className="text-gray-700 mb-4">
              We process personal data based on:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Your consent when you voluntarily provide information</li>
              <li>Legitimate interest in communicating with potential and existing clients</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              4. Data Sharing
            </h2>
            <p className="text-gray-700 mb-4">
              We do not sell, rent, or share your personal data with third parties, except:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>When required by law</li>
              <li>When necessary to provide our services (e.g., booking systems), under confidentiality obligations</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              5. Data Storage and Protection
            </h2>
            <p className="text-gray-700">
              We take reasonable measures to protect your personal data from unauthorized access, loss, misuse, or disclosure. Data is stored securely and accessed only by authorized personnel.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              6. Data Retention
            </h2>
            <p className="text-gray-700">
              We retain personal data only for as long as necessary to fulfill the purposes outlined in this policy or as required by law.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              7. Your Rights
            </h2>
            <p className="text-gray-700 mb-4">
              You have the right to:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Request access to your personal data</li>
              <li>Request correction or deletion of your data</li>
              <li>Withdraw consent at any time</li>
            </ul>
            <p className="text-gray-700 mt-4">
              To exercise these rights, please contact us via Instagram direct message.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              8. Changes to This Policy
            </h2>
            <p className="text-gray-700">
              We may update this Privacy Policy from time to time. Any changes will be communicated through our Instagram account.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              9. Contact Information
            </h2>
            <p className="text-gray-700">
              If you have any questions about this Privacy Policy or our data practices, please contact us via our official Instagram account.
            </p>
          </section>
        </div>

        <div className="mt-12 pt-8 border-t border-gray-200">
          <p className="text-sm text-gray-500">
            Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>
      </div>
    </div>
  );
}

