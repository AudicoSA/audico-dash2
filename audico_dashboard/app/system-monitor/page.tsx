
'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useToast } from '@/hooks/use-toast'
import { 
  Activity, 
  Server, 
  Database, 
  Cloud, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  RefreshCw,
  Download,
  Filter,
  Clock,
  Cpu,
  HardDrive,
  Wifi
} from 'lucide-react'

interface SystemMetric {
  name: string
  value: string
  status: 'healthy' | 'warning' | 'error'
  lastUpdated: string
}

interface LogEntry {
  id: string
  timestamp: string
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG'
  component: string
  message: string
  details?: string
}

export default function SystemMonitor() {
  const [metrics, setMetrics] = useState<SystemMetric[]>([])
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [logFilter, setLogFilter] = useState<string>('all')
  const { toast } = useToast()

  // Mock system metrics
  const mockMetrics: SystemMetric[] = [
    {
      name: 'Google Cloud Storage',
      value: 'Connected',
      status: 'healthy',
      lastUpdated: new Date().toISOString()
    },
    {
      name: 'Document AI API',
      value: 'Connected',
      status: 'healthy',
      lastUpdated: new Date().toISOString()
    },
    {
      name: 'OpenCart API',
      value: 'Connected',
      status: 'healthy',
      lastUpdated: new Date().toISOString()
    },
    {
      name: 'Processing Queue',
      value: '3 pending',
      status: 'warning',
      lastUpdated: new Date().toISOString()
    },
    {
      name: 'Error Rate',
      value: '1.2%',
      status: 'healthy',
      lastUpdated: new Date().toISOString()
    },
    {
      name: 'Response Time',
      value: '245ms',
      status: 'healthy',
      lastUpdated: new Date().toISOString()
    }
  ]

  // Mock log entries
  const mockLogs: LogEntry[] = [
    {
      id: '1',
      timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
      level: 'INFO',
      component: 'Orchestrator',
      message: 'Starting full pipeline execution',
      details: 'Processing 3 files from GCS bucket'
    },
    {
      id: '2',
      timestamp: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
      level: 'INFO',
      component: 'DocumentAI',
      message: 'Successfully parsed pricelist_2024_05_28.pdf',
      details: 'Found 45 products, processing time: 3.2s'
    },
    {
      id: '3',
      timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
      level: 'WARNING',
      component: 'ProductSync',
      message: 'Price mismatch detected for product AUD-XM-2000',
      details: 'Parsed price: $2599.99, Existing price: $2499.99'
    },
    {
      id: '4',
      timestamp: new Date(Date.now() - 20 * 60 * 1000).toISOString(),
      level: 'ERROR',
      component: 'OpenCartAPI',
      message: 'Failed to create product: Invalid SKU format',
      details: 'SKU "AUD-INVALID-" does not match required pattern'
    },
    {
      id: '5',
      timestamp: new Date(Date.now() - 25 * 60 * 1000).toISOString(),
      level: 'INFO',
      component: 'GCSClient',
      message: 'File moved to processed folder',
      details: 'pricelist_2024_05_27.xlsx -> processed/pricelist_2024_05_27.xlsx'
    },
    {
      id: '6',
      timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
      level: 'DEBUG',
      component: 'ProductLogic',
      message: 'Product similarity calculation completed',
      details: 'Compared 45 parsed products with 1,234 existing products'
    }
  ]

  useEffect(() => {
    setMetrics(mockMetrics)
    setLogs(mockLogs)
  }, [])

  const refreshMetrics = async () => {
    setIsRefreshing(true)
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // Update timestamps
    const updatedMetrics = mockMetrics.map(metric => ({
      ...metric,
      lastUpdated: new Date().toISOString()
    }))
    
    setMetrics(updatedMetrics)
    setIsRefreshing(false)
    
    toast({
      title: "Metrics refreshed",
      description: "System metrics have been updated",
    })
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
        return <Badge className="bg-green-100 text-green-800">Healthy</Badge>
      case 'warning':
        return <Badge className="bg-yellow-100 text-yellow-800">Warning</Badge>
      case 'error':
        return <Badge className="bg-red-100 text-red-800">Error</Badge>
      default:
        return <Badge>Unknown</Badge>
    }
  }

  const getLogLevelBadge = (level: string) => {
    switch (level) {
      case 'INFO':
        return <Badge className="bg-blue-100 text-blue-800">INFO</Badge>
      case 'WARNING':
        return <Badge className="bg-yellow-100 text-yellow-800">WARNING</Badge>
      case 'ERROR':
        return <Badge className="bg-red-100 text-red-800">ERROR</Badge>
      case 'DEBUG':
        return <Badge className="bg-gray-100 text-gray-800">DEBUG</Badge>
      default:
        return <Badge>UNKNOWN</Badge>
    }
  }

  const filteredLogs = logs.filter(log => 
    logFilter === 'all' || log.level === logFilter
  )

  const systemStats = {
    uptime: '99.8%',
    totalRequests: '12,456',
    avgResponseTime: '245ms',
    errorRate: '1.2%'
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-2"
      >
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Activity className="h-8 w-8 text-orange-500" />
          System Monitor
        </h1>
        <p className="text-muted-foreground">
          Monitor system status, performance metrics, and view detailed logs
        </p>
      </motion.div>

      {/* System Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-4 gap-4"
      >
        <Card className="bg-gradient-to-br from-blue-500 to-cyan-500 text-white border-0 shadow-lg">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm">Uptime</p>
                <p className="text-2xl font-bold">{systemStats.uptime}</p>
              </div>
              <Server className="h-8 w-8 text-blue-200" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-green-500 to-emerald-500 text-white border-0 shadow-lg">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-100 text-sm">Total Requests</p>
                <p className="text-2xl font-bold">{systemStats.totalRequests}</p>
              </div>
              <Wifi className="h-8 w-8 text-green-200" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-purple-500 to-violet-500 text-white border-0 shadow-lg">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100 text-sm">Avg Response</p>
                <p className="text-2xl font-bold">{systemStats.avgResponseTime}</p>
              </div>
              <Cpu className="h-8 w-8 text-purple-200" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-orange-500 to-red-500 text-white border-0 shadow-lg">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-100 text-sm">Error Rate</p>
                <p className="text-2xl font-bold">{systemStats.errorRate}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-orange-200" />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Main Content */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Tabs defaultValue="metrics" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="metrics">System Metrics</TabsTrigger>
            <TabsTrigger value="logs">System Logs</TabsTrigger>
          </TabsList>
          
          <TabsContent value="metrics" className="space-y-4">
            <Card className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  System Health Metrics
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={refreshMetrics}
                    disabled={isRefreshing}
                  >
                    {isRefreshing ? (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="h-4 w-4" />
                    )}
                  </Button>
                </CardTitle>
                <CardDescription>
                  Real-time status of all system components
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {metrics.map((metric, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-medium">{metric.name}</h3>
                        {getStatusIcon(metric.status)}
                      </div>
                      <p className="text-2xl font-bold mb-1">{metric.value}</p>
                      <div className="flex items-center justify-between">
                        {getStatusBadge(metric.status)}
                        <span className="text-xs text-muted-foreground">
                          {new Date(metric.lastUpdated).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="logs" className="space-y-4">
            <Card className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  System Logs
                  <div className="flex gap-2">
                    <Button
                      variant={logFilter === 'all' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setLogFilter('all')}
                    >
                      All
                    </Button>
                    <Button
                      variant={logFilter === 'ERROR' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setLogFilter('ERROR')}
                    >
                      Errors
                    </Button>
                    <Button
                      variant={logFilter === 'WARNING' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setLogFilter('WARNING')}
                    >
                      Warnings
                    </Button>
                    <Button variant="outline" size="sm">
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                </CardTitle>
                <CardDescription>
                  Recent system activity and error logs
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-96">
                  <div className="space-y-3">
                    {filteredLogs.map((log) => (
                      <div key={log.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            {getLogLevelBadge(log.level)}
                            <span className="font-medium">{log.component}</span>
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {new Date(log.timestamp).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-sm mb-2">{log.message}</p>
                        {log.details && (
                          <p className="text-xs text-muted-foreground bg-slate-50 dark:bg-slate-800 p-2 rounded">
                            {log.details}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  )
}
