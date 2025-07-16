// 滚动区域组件
import * as React from "react"
import { cn } from "@/lib/utils"

interface ScrollAreaProps {
  children: React.ReactNode
  className?: string
}

export function ScrollArea({ children, className }: ScrollAreaProps) {
  return (
    <div className={cn("relative overflow-hidden", className)}>
      <div className="h-full w-full overflow-auto">
        {children}
      </div>
    </div>
  )
}

export function ScrollBar() {
  return null
}