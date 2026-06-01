import { createContext, useContext, useId, type ButtonHTMLAttributes, type HTMLAttributes, type ReactNode } from 'react'

interface TabsContextValue {
  value: string
  baseId: string
  onValueChange: (value: string) => void
}

const TabsContext = createContext<TabsContextValue | null>(null)

function useTabsContext() {
  const context = useContext(TabsContext)
  if (!context) {
    throw new Error('Tabs components must be used within <Tabs />')
  }
  return context
}

interface TabsProps {
  value: string
  onValueChange: (value: string) => void
  children: ReactNode
  className?: string
}

export function Tabs({ value, onValueChange, children, className = '' }: TabsProps) {
  const baseId = useId()

  return (
    <TabsContext.Provider value={{ value, onValueChange, baseId }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  )
}

export function TabsList({ className = '', ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      role="tablist"
      className={`inline-flex w-full flex-wrap gap-2 rounded-lg border border-border bg-muted/40 p-1 ${className}`}
      {...props}
    />
  )
}

interface TabsTriggerProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  value: string
}

export function TabsTrigger({ value, className = '', ...props }: TabsTriggerProps) {
  const { value: currentValue, onValueChange, baseId } = useTabsContext()
  const isSelected = currentValue === value

  return (
    <button
      type="button"
      role="tab"
      id={`${baseId}-trigger-${value}`}
      aria-controls={`${baseId}-content-${value}`}
      aria-selected={isSelected}
      tabIndex={isSelected ? 0 : -1}
      className={`inline-flex min-h-10 flex-1 items-center justify-center rounded-md px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
        isSelected
          ? 'bg-card text-foreground shadow-sm'
          : 'text-muted-foreground hover:bg-background hover:text-foreground'
      } ${className}`}
      onClick={() => onValueChange(value)}
      {...props}
    />
  )
}

interface TabsContentProps extends HTMLAttributes<HTMLDivElement> {
  value: string
}

export function TabsContent({ value, className = '', ...props }: TabsContentProps) {
  const { value: currentValue, baseId } = useTabsContext()

  if (currentValue !== value) {
    return null
  }

  return (
    <div
      role="tabpanel"
      id={`${baseId}-content-${value}`}
      aria-labelledby={`${baseId}-trigger-${value}`}
      className={className}
      {...props}
    />
  )
}
