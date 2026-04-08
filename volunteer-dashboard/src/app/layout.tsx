import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'VolunteerFinder — Find Opportunities Near You',
  description: 'Search volunteer opportunities by location and category.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 min-h-screen">{children}</body>
    </html>
  );
}
