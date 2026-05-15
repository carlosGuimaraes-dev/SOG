import { type HTMLAttributes, forwardRef } from 'react'

interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'destructive' | 'warning'
}

const Alert = forwardRef<HTMLDivElement, AlertProps>(
  ({ className = '', variant = 'default', ...props }, ref) => {
    const variants = {
      default: 'bg-background text-foreground border-border',
      destructive: 'border-destructive/50 text-destructive dark:border-destructive [&>svg]:text-destructive',
      warning: 'border-warning/50 text-warning-foreground bg-warning/10',
    }
    return (
      <div
        ref={ref}
        role="alert"
        className={`relative w-full rounded-lg border p-4 [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg+div]:translate-y-[-3px] [&:has(svg)]:pl-11 ${variants[variant]} ${className}`}
        {...props}
      />
    )
  }
)
Alert.displayName = 'Alert'

export const AlertTitle = forwardRef<HTMLHeadingElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className = '', ...props }, ref) => (
    <h5 ref={ref} className={`mb-1 font-medium leading-none tracking-tight ${className}`} {...props} />
  )
)
AlertTitle.displayName = 'AlertTitle'

export const AlertDescription = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className = '', ...props }, ref) => (
    <div ref={ref} className={`text-sm opacity-90 ${className}`} {...props} />
  )
)
AlertDescription.displayName = 'AlertDescription'

export default Alert
