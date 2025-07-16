// 面包屑导航组件
import { cn } from "@/lib/utils"

interface BreadcrumbProps {
  children: React.ReactNode
  className?: string
}

export function Breadcrumb({ children, className }: BreadcrumbProps) {
  return (
    <nav className={cn('flex', className)} aria-label="breadcrumb">
      {children}
    </nav>
  )
}

interface BreadcrumbListProps {
  children: React.ReactNode
  className?: string
}

export function BreadcrumbList({ children, className }: BreadcrumbListProps) {
  return (
    <ol className={cn('flex items-center space-x-2', className)}>
      {children}
    </ol>
  )
}

interface BreadcrumbItemProps {
  children: React.ReactNode
  className?: string
}

export function BreadcrumbItem({ children, className }: BreadcrumbItemProps) {
  return (
    <li className={cn('flex items-center', className)}>
      {children}
    </li>
  )
}

interface BreadcrumbLinkProps {
  children: React.ReactNode
  className?: string
  href?: string
}

export function BreadcrumbLink({ children, className, href }: BreadcrumbLinkProps) {
  return (
    <a href={href} className={cn('text-muted-foreground hover:text-foreground', className)}>
      {children}
    </a>
  )
}

interface BreadcrumbSeparatorProps {
  children?: React.ReactNode
  className?: string
}

export function BreadcrumbSeparator({ children, className }: BreadcrumbSeparatorProps) {
  return (
    <span className={cn('text-muted-foreground', className)}>
      {children || '/'}
    </span>
  )
}

interface BreadcrumbPageProps {
  children: React.ReactNode
  className?: string
}

export function BreadcrumbPage({ children, className }: BreadcrumbPageProps) {
  return (
    <span className={cn('font-normal text-foreground', className)}>
      {children}
    </span>
  )
}