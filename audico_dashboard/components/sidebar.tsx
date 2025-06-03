
'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { 
  Home,
  FileText, 
  ShoppingCart, 
  GitCompare, 
  Activity, 
  Settings, 
  PlayCircle,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'

const navigation = [
  {
    name: 'Dashboard',
    href: '/',
    icon: Home
  },
  {
    name: 'Pricelist Testing',
    href: '/pricelist-testing',
    icon: FileText
  },
  {
    name: 'OpenCart Integration',
    href: '/opencart-integration',
    icon: ShoppingCart
  },
  {
    name: 'Product Comparison',
    href: '/product-comparison',
    icon: GitCompare
  },
  {
    name: 'System Monitor',
    href: '/system-monitor',
    icon: Activity
  },
  {
    name: 'Configuration',
    href: '/configuration',
    icon: Settings
  },
  {
    name: 'Dry Run Operations',
    href: '/dry-run',
    icon: PlayCircle
  }
]

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const pathname = usePathname()

  return (
    <motion.div
      initial={{ x: -300 }}
      animate={{ x: 0 }}
      className={cn(
        "bg-gradient-to-b from-slate-900 to-slate-800 text-white transition-all duration-300 flex flex-col shadow-2xl",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Header */}
      <div className="p-4 border-b border-slate-700">
        <div className="flex items-center justify-between">
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-2"
            >
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">A</span>
              </div>
              <span className="font-bold text-lg">Audico Dashboard</span>
            </motion.div>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setCollapsed(!collapsed)}
            className="text-white hover:bg-slate-700"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link key={item.name} href={item.href}>
              <motion.div
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 group",
                  isActive 
                    ? "bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg" 
                    : "hover:bg-slate-700 text-slate-300 hover:text-white"
                )}
              >
                <item.icon className={cn(
                  "h-5 w-5 transition-colors",
                  isActive ? "text-white" : "text-slate-400 group-hover:text-white"
                )} />
                {!collapsed && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="font-medium"
                  >
                    {item.name}
                  </motion.span>
                )}
              </motion.div>
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-slate-700">
        {!collapsed && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-xs text-slate-400 text-center"
          >
            <p>Audico Product Manager</p>
            <p>Testing Dashboard v1.0</p>
          </motion.div>
        )}
      </div>
    </motion.div>
  )
}
