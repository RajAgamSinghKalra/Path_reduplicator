"use client"

import type React from "react"
import { useEffect, useRef, useState } from "react"
import { cn } from "@/lib/utils"

interface AnimatedContainerProps {
  children: React.ReactNode
  className?: string
  animation?: "fade-in" | "slide-up" | "slide-in-left" | "scale-in"
  delay?: number
  threshold?: number
}

export function AnimatedContainer({
  children,
  className,
  animation = "fade-in",
  delay = 0,
  threshold = 0.1,
}: AnimatedContainerProps) {
  const [isVisible, setIsVisible] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setTimeout(() => setIsVisible(true), delay)
        }
      },
      { threshold },
    )

    if (ref.current) {
      observer.observe(ref.current)
    }

    return () => observer.disconnect()
  }, [delay, threshold])

  const animationClass = {
    "fade-in": "animate-fade-in",
    "slide-up": "animate-slide-up",
    "slide-in-left": "animate-slide-in-left",
    "scale-in": "animate-scale-in",
  }[animation]

  return (
    <div ref={ref} className={cn("opacity-0", isVisible && animationClass, className)}>
      {children}
    </div>
  )
}
