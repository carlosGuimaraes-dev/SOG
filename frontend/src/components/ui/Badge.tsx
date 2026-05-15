import { type HTMLAttributes, forwardRef } from 'react'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning'
}

const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className = '', variant = 'default', ...props }, ref) => {
    const variants = {
      default: 'bg-primary text-primary-foreground hover:bg-primary/80',
      secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
      destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/80',
      outline: 'text-foreground border border-input hover:bg-accent hover:text-accent-foreground',
      success: 'bg-success text-success-foreground hover:bg-success/80',
      warning: 'bg-warning text-warning-foreground hover:bg-warning/80',
    }
    return (
      <span
        ref={ref}
        className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors ${variants[variant]} ${className}`}
        {...props}
      />
    )
  }
)
Badge.displayName = 'Badge'
export default Badge
