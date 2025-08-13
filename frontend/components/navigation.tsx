"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Shield, DollarSign } from "lucide-react"
import { cn } from "@/lib/utils"
import { ThemeToggle } from "./theme-toggle"

const navigation = [
  { name: "Dashboard", href: "/" },
  { name: "Onboard Applicant", href: "/onboard-applicant" },
  { name: "Duplicate Check", href: "/duplicate-check" },
  { name: "Train Model", href: "/train-model" },
]

export function Navigation() {
  const pathname = usePathname()

  return (
    <nav className="glass-nav sticky top-0 z-50 transition-all duration-500">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="flex items-center space-x-2 group">
              <div className="relative transition-all duration-500 group-hover:scale-110">
                <div className="absolute inset-0 bg-gradient-to-r from-galaxy-purple via-galaxy-pink to-galaxy-cyan rounded-full blur-md opacity-30 group-hover:opacity-50 transition-opacity duration-300"></div>
                <Shield className="relative h-8 w-8 text-primary transition-all duration-300 group-hover:text-galaxy-purple" />
                <DollarSign className="absolute h-4 w-4 text-accent top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 transition-all duration-300 group-hover:text-galaxy-cyan" />
              </div>
              <span className="text-xl font-bold font-montserrat transition-all duration-300 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-galaxy-purple group-hover:to-galaxy-pink">
                Loan Dedupe Portal
              </span>
            </Link>
          </div>

          <div className="flex items-center space-x-6">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "px-4 py-2 rounded-xl text-sm font-medium font-open-sans transition-all duration-300 hover-glass relative overflow-hidden group",
                  pathname === item.href
                    ? "glass-card text-primary shadow-lg animate-galaxy-pulse"
                    : "text-foreground hover:text-primary hover:scale-105",
                )}
              >
                <span className="absolute inset-0 bg-gradient-galaxy-subtle opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-xl"></span>
                <span className="relative z-10">{item.name}</span>
              </Link>
            ))}
            <div className="ml-2">
              <ThemeToggle />
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}
