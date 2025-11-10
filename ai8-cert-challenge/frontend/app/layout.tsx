import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Scout - School Events Assistant',
  description: 'AI-powered school events assistant',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

