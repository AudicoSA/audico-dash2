
'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/hooks/use-toast'
import { 
  Settings, 
  Cloud, 
  Database, 
  ShoppingCart, 
  TestTube, 
  Save, 
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertTriangle
} from 'lucide-react'

interface ConnectionTest {
  service: string
  status: 'testing' | 'success' | 'error'
  message: string
}

export default function Configuration() {
  const [config, setConfig] = useState({
    // Google Cloud Settings
    googleCloudProjectId: 'audico-pricelists',
    googleCloudLocation: 'us',
    googleCloudProcessorId: '',
    gcsCredentialsPath: './credentials/audico-pricelists-credentials.json',
    gcsBucketName: 'audicopricelistingest',
    
    // OpenCart Settings
    openCartBaseUrl: 'https://www.audicoonline.co.za/index.php?route=ocrestapi/product',
    openCartAuthToken: 'b2NyZXN0YXBpX29hdXRoX2NsaWVudDpvY3Jlc3RhcGlfb2F1dGhfc2VjcmV0',
    
    // Processing Settings
    targetCategory: 'Load',
    defaultManufacturer: 'Audico',
    batchSize: 50,
    maxRetries: 3,
    retryDelay: 5,
    
    // Advanced Settings
    logLevel: 'INFO',
    enableDryRun: false,
    autoProcessFiles: true,
    enableNotifications: true
  })

  const [connectionTests, setConnectionTests] = useState<ConnectionTest[]>([])
  const [isSaving, setIsSaving] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const { toast } = useToast()

  const handleConfigChange = (key: string, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }))
  }

  const saveConfiguration = async () => {
    setIsSaving(true)
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    setIsSaving(false)
    
    toast({
      title: "Configuration saved",
      description: "All settings have been updated successfully",
    })
  }

  const testConnections = async () => {
    setIsTesting(true)
    setConnectionTests([
      { service: 'Google Cloud Storage', status: 'testing', message: 'Testing connection...' },
      { service: 'Document AI', status: 'testing', message: 'Testing connection...' },
      { service: 'OpenCart API', status: 'testing', message: 'Testing connection...' }
    ])

    // Simulate testing each service
    const services = ['Google Cloud Storage', 'Document AI', 'OpenCart API']
    
    for (let i = 0; i < services.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      setConnectionTests(prev => prev.map(test => 
        test.service === services[i] 
          ? { 
              ...test, 
              status: Math.random() > 0.2 ? 'success' : 'error',
              message: Math.random() > 0.2 ? 'Connection successful' : 'Connection failed'
            }
          : test
      ))
    }
    
    setIsTesting(false)
    
    toast({
      title: "Connection tests completed",
      description: "Check the results below",
    })
  }

  const getConnectionIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'testing':
        return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-500" />
    }
  }

  const getConnectionBadge = (status: string) => {
    switch (status) {
      case 'success':
        return <Badge className="bg-green-100 text-green-800">Connected</Badge>
      case 'error':
        return <Badge className="bg-red-100 text-red-800">Failed</Badge>
      case 'testing':
        return <Badge className="bg-blue-100 text-blue-800">Testing</Badge>
      default:
        return <Badge className="bg-gray-100 text-gray-800">Unknown</Badge>
    }
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
          <Settings className="h-8 w-8 text-gray-500" />
          Configuration
        </h1>
        <p className="text-muted-foreground">
          Configure system settings and test service connections
        </p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Settings */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-2"
        >
          <Card className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader>
              <CardTitle>System Configuration</CardTitle>
              <CardDescription>
                Configure all system settings and service connections
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="google-cloud" className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="google-cloud">Google Cloud</TabsTrigger>
                  <TabsTrigger value="opencart">OpenCart</TabsTrigger>
                  <TabsTrigger value="processing">Processing</TabsTrigger>
                  <TabsTrigger value="advanced">Advanced</TabsTrigger>
                </TabsList>
                
                <TabsContent value="google-cloud" className="space-y-4">
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="project-id">Project ID</Label>
                        <Input
                          id="project-id"
                          value={config.googleCloudProjectId}
                          onChange={(e) => handleConfigChange('googleCloudProjectId', e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="location">Location</Label>
                        <Select value={config.googleCloudLocation} onValueChange={(value) => handleConfigChange('googleCloudLocation', value)}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="us">US</SelectItem>
                            <SelectItem value="eu">EU</SelectItem>
                            <SelectItem value="asia">Asia</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="processor-id">Document AI Processor ID</Label>
                      <Input
                        id="processor-id"
                        value={config.googleCloudProcessorId}
                        onChange={(e) => handleConfigChange('googleCloudProcessorId', e.target.value)}
                        placeholder="Enter processor ID"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="credentials-path">Credentials File Path</Label>
                      <Input
                        id="credentials-path"
                        value={config.gcsCredentialsPath}
                        onChange={(e) => handleConfigChange('gcsCredentialsPath', e.target.value)}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="bucket-name">GCS Bucket Name</Label>
                      <Input
                        id="bucket-name"
                        value={config.gcsBucketName}
                        onChange={(e) => handleConfigChange('gcsBucketName', e.target.value)}
                      />
                    </div>
                  </div>
                </TabsContent>
                
                <TabsContent value="opencart" className="space-y-4">
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="opencart-url">OpenCart Base URL</Label>
                      <Input
                        id="opencart-url"
                        value={config.openCartBaseUrl}
                        onChange={(e) => handleConfigChange('openCartBaseUrl', e.target.value)}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="auth-token">Authentication Token</Label>
                      <Textarea
                        id="auth-token"
                        value={config.openCartAuthToken}
                        onChange={(e) => handleConfigChange('openCartAuthToken', e.target.value)}
                        rows={3}
                      />
                    </div>
                  </div>
                </TabsContent>
                
                <TabsContent value="processing" className="space-y-4">
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="target-category">Target Category</Label>
                        <Input
                          id="target-category"
                          value={config.targetCategory}
                          onChange={(e) => handleConfigChange('targetCategory', e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="manufacturer">Default Manufacturer</Label>
                        <Input
                          id="manufacturer"
                          value={config.defaultManufacturer}
                          onChange={(e) => handleConfigChange('defaultManufacturer', e.target.value)}
                        />
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="batch-size">Batch Size</Label>
                        <Input
                          id="batch-size"
                          type="number"
                          value={config.batchSize}
                          onChange={(e) => handleConfigChange('batchSize', parseInt(e.target.value))}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="max-retries">Max Retries</Label>
                        <Input
                          id="max-retries"
                          type="number"
                          value={config.maxRetries}
                          onChange={(e) => handleConfigChange('maxRetries', parseInt(e.target.value))}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="retry-delay">Retry Delay (s)</Label>
                        <Input
                          id="retry-delay"
                          type="number"
                          value={config.retryDelay}
                          onChange={(e) => handleConfigChange('retryDelay', parseInt(e.target.value))}
                        />
                      </div>
                    </div>
                  </div>
                </TabsContent>
                
                <TabsContent value="advanced" className="space-y-4">
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="log-level">Log Level</Label>
                      <Select value={config.logLevel} onValueChange={(value) => handleConfigChange('logLevel', value)}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="DEBUG">DEBUG</SelectItem>
                          <SelectItem value="INFO">INFO</SelectItem>
                          <SelectItem value="WARNING">WARNING</SelectItem>
                          <SelectItem value="ERROR">ERROR</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>Enable Dry Run Mode</Label>
                          <p className="text-sm text-muted-foreground">
                            Analyze changes without executing them
                          </p>
                        </div>
                        <Switch
                          checked={config.enableDryRun}
                          onCheckedChange={(checked) => handleConfigChange('enableDryRun', checked)}
                        />
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>Auto Process Files</Label>
                          <p className="text-sm text-muted-foreground">
                            Automatically process new files in GCS bucket
                          </p>
                        </div>
                        <Switch
                          checked={config.autoProcessFiles}
                          onCheckedChange={(checked) => handleConfigChange('autoProcessFiles', checked)}
                        />
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>Enable Notifications</Label>
                          <p className="text-sm text-muted-foreground">
                            Send notifications for processing results
                          </p>
                        </div>
                        <Switch
                          checked={config.enableNotifications}
                          onCheckedChange={(checked) => handleConfigChange('enableNotifications', checked)}
                        />
                      </div>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
              
              <div className="flex gap-2 mt-6">
                <Button onClick={saveConfiguration} disabled={isSaving}>
                  {isSaving ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-2" />
                      Save Configuration
                    </>
                  )}
                </Button>
                <Button variant="outline" onClick={testConnections} disabled={isTesting}>
                  {isTesting ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Testing...
                    </>
                  ) : (
                    <>
                      <TestTube className="h-4 w-4 mr-2" />
                      Test Connections
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Connection Tests */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader>
              <CardTitle>Connection Tests</CardTitle>
              <CardDescription>
                Test connectivity to all external services
              </CardDescription>
            </CardHeader>
            <CardContent>
              {connectionTests.length > 0 ? (
                <div className="space-y-4">
                  {connectionTests.map((test, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          {getConnectionIcon(test.status)}
                          <span className="font-medium">{test.service}</span>
                        </div>
                        {getConnectionBadge(test.status)}
                      </div>
                      <p className="text-sm text-muted-foreground">{test.message}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <TestTube className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-lg font-medium mb-2">No tests run</p>
                  <p className="text-muted-foreground">
                    Click "Test Connections" to check service connectivity
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}
