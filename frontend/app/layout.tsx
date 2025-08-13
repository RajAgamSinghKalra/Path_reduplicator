import type React from "react"
import type { Metadata } from "next"
import { Inter, Montserrat, Open_Sans } from "next/font/google"
import { ThemeProvider } from "@/lib/theme-context"
import "./globals.css"

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
})

const montserrat = Montserrat({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-montserrat",
  weight: ["400", "600", "700", "900"], // Added Black weight (900)
})

const openSans = Open_Sans({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-open-sans",
  weight: ["400", "500", "600"],
})

export const metadata: Metadata = {
  title: "Loan Dedupe Portal - Banking Duplicate Detection",
  description: "Advanced loan applicant duplicate detection system for banking institutions",
  generator: "v0.app",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${montserrat.variable} ${openSans.variable} antialiased`}>
      <body className="font-open-sans transition-colors duration-300">
        {/* Wrapped children in ThemeProvider */}
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  )
}
