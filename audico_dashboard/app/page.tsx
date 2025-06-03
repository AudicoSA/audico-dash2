'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  FileText, 
  ShoppingCart, 
  GitCompare, 
  Activity, 
  Settings, 
  PlayCircle,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  Database,
  Cloud
} from 'lucide-react'
import Link from 'next/link'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
}

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      duration: 0.5
    }
  }
}

export default function Dashboard() {
  const [systemStatus, setSystemStatus] = useState({
    gcs: 'checking',
    document_ai: 'checking',
    opencart: 'checking'
  })

  const [stats, setStats] = useState({
    filesProcessed: 0,
    productsAnalyzed: 0,
    lastSync: null as string | null,
    pendingFiles: 0
  })

  useEffect(() => {
    // Simulate checking system status
    const checkStatus = async () => {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      setSystemStatus({
        gcs: 'connected',
        document_ai: 'connected',
        opencart: 'connected'
      })
      
      setStats({
        filesProcessed: 127,
        productsAnalyzed: 2456,
        lastSync: new Date().toISOString(),
        pendingFiles: 3
      })
    }

    checkStatus()
  }, [])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-yellow-500 animate-spin" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'error':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      default:
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
    }
  }

  const features = [
    {
      title: 'Pricelist Testing',
      description: 'Upload and test pricelist files with Document AI parsing',
      icon: FileText,
      href: '/pricelist-testing',
      color: 'from-blue-500 to-cyan-500'
    },
    {
      title: 'OpenCart Integration',
      description: 'Test product creation and updates to OpenCart store',
      icon: ShoppingCart,
      href: '/opencart-integration',
      color: 'from-green-500 to-emerald-500'
    },
    {
      title: 'Product Comparison',
      description: 'Compare parsed data with existing store products',
      icon: GitCompare,
      href: '/product-comparison',
      color: 'from-purple-500 to-violet-500'
    },
    {
      title: 'System Monitor',
      description: 'Monitor system status and view detailed logs',
      icon: Activity,
      href: '/system-monitor',
      color: 'from-orange-500 to-red-500'
    },
    {
      title: 'Configuration',
      description: 'Configure system settings and test connections',
      icon: Settings,
      href: '/configuration',
      color: 'from-gray-500 to-slate-500'
    },
    {
      title: 'Dry Run Operations',
      description: 'Run safe operations without making actual changes',
      icon: PlayCircle,
      href: '/dry-run',
      color: 'from-indigo-500 to-blue-500'
    }
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-2"
      >
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          Audico Product Management Dashboard
        </h1>
        <p className="text-lg text-muted-foreground">
          Test and monitor your automated product management system
        </p>
      </motion.div>

      {/* System Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              System Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-700">
                <div className="flex items-center gap-2">
                  <Cloud className="h-4 w-4" />
                  <span className="font-medium">Google Cloud Storage</span>
                </div>
                <Badge className={getStatusColor(systemStatus.gcs)}>
                  {getStatusIcon(systemStatus.gcs)}
                  {systemStatus.gcs}
                </Badge>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-700">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  <span className="font-medium">Document AI</span>
                </div>
                <Badge className={getStatusColor(systemStatus.document_ai)}>
                  {getStatusIcon(systemStatus.document_ai)}
                  {systemStatus.document_ai}
                </Badge>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-700">
                <div className="flex items-center gap-2">
                  <ShoppingCart className="h-4 w-4" />
                  <span className="font-medium">OpenCart API</span>
                </div>
                <Badge className={getStatusColor(systemStatus.opencart)}>
                  {getStatusIcon(systemStatus.opencart)}
                  {systemStatus.opencart}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="grid grid-cols-1 md:grid-cols-4 gap-4"
      >
        <Card className="bg-gradient-to-br from-blue-500 to-cyan-500 text-white border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100">Files Processed</p>
                <p className="text-3xl font-bold">{stats.filesProcessed}</p>
              </div>
              <FileText className="h-8 w-8 text-blue-200" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-green-500 to-emerald-500 text-white border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-100">Products Analyzed</p>
                <p className="text-3xl font-bold">{stats.productsAnalyzed}</p>
              </div>
              <Database className="h-8 w-8 text-green-200" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-purple-500 to-violet-500 text-white border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100">Pending Files</p>
                <p className="text-3xl font-bold">{stats.pendingFiles}</p>
              </div>
              <Clock className="h-8 w-8 text-purple-200" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-orange-500 to-red-500 text-white border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-100">Success Rate</p>
                <p className="text-3xl font-bold">98.5%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-orange-200" />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Features Grid */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
      >
        {features.map((feature, index) => (
          <motion.div key={feature.title} variants={itemVariants}>
            <Link href={feature.href}>
              <Card className="group hover:shadow-xl transition-all duration-300 cursor-pointer bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-0 shadow-lg hover:scale-105">
                <CardHeader>
                  <div className={`w-12 h-12 rounded-lg bg-gradient-to-r ${feature.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                    <feature.icon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle className="group-hover:text-primary transition-colors">
                    {feature.title}
                  </CardTitle>
                  <CardDescription>{feature.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button variant="ghost" className="w-full group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                    Open Module
                  </Button>
                </CardContent>
              </Card>
            </Link>
          </motion.div>
        ))}
      </motion.div>
    </div>
  )
}
