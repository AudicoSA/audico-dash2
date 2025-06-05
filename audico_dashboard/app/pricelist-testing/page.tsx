
'use client'

import { useState, useCallback, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Progress } from '@/components/ui/progress'
import { useToast } from '@/hooks/use-toast'
import { OpenCartAPI } from '@/lib/api'
import { ParsedProduct, FileUploadResult, ProductComparison } from '@/lib/types'
import { 
  Upload, 
  FileText, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Download,
  Eye,
  AlertTriangle,
  Loader2,
  Wifi,
  WifiOff,
  RefreshCw,
  GitCompare
} from 'lucide-react'

export default function PricelistTesting() {
  const [uploadResults, setUploadResults] = useState<FileUploadResult[]>([])
  const [selectedFile, setSelectedFile] = useState<FileUploadResult | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [backendStatus, setBackendStatus] = useState<'connected' | 'disconnected' | 'testing'>('disconnected')
  const [comparisonResult, setComparisonResult] = useState<ProductComparison | null>(null)
  const [isComparing, setIsComparing] = useState(false)
  const { toast } = useToast()

  // Test backend connection on component mount
  useEffect(() => {
    testBackendConnection()
  }, [])

  const testBackendConnection = async () => {
    setBackendStatus('testing')
    try {
      const result = await OpenCartAPI.testBackendConnection()
      if (result.success) {
        setBackendStatus('connected')
        toast({
          title: "Backend connected",
          description: "Successfully connected to the processing backend",
        })
      } else {
        setBackendStatus('disconnected')
        toast({
          title: "Backend connection failed",
          description: result.error || "Failed to connect to processing backend",
          variant: "destructive"
        })
      }
    } catch (error) {
      setBackendStatus('disconnected')
      toast({
        title: "Backend connection error",
        description: "Unable to reach processing backend",
        variant: "destructive"
      })
    }
  }

  const handleProductComparison = async (fileResult: FileUploadResult) => {
    if (!fileResult.products || fileResult.products.length === 0) {
      toast({
        title: "No products to compare",
        description: "The selected file has no parsed products",
        variant: "destructive"
      })
      return
    }

    setIsComparing(true)
    try {
      const result = await OpenCartAPI.compareProducts(fileResult.products)
      
      if (result.success && result.data) {
        setComparisonResult(result.data)
        toast({
          title: "Comparison completed",
          description: `Found ${result.data.summary.addCount} products to add, ${result.data.summary.updateCount} to update, ${result.data.summary.removeCount} to remove`,
        })
      } else {
        toast({
          title: "Comparison failed",
          description: result.error || "Failed to compare products",
          variant: "destructive"
        })
      }
    } catch (error) {
      toast({
        title: "Comparison error",
        description: error instanceof Error ? error.message : "Unknown error occurred",
        variant: "destructive"
      })
    } finally {
      setIsComparing(false)
    }
  }

  const handleFileUpload = useCallback(async (files: FileList) => {
    if (backendStatus !== 'connected') {
      toast({
        title: "Backend not connected",
        description: "Please ensure the backend is running and connected",
        variant: "destructive"
      })
      return
    }

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      const result: FileUploadResult = {
        fileName: file.name,
        status: 'processing',
        progress: 0
      }
      
      setUploadResults(prev => [...prev, result])
      
      try {
        // Start processing with real API call
        const startTime = Date.now()
        
        // Simulate progress updates while processing
        const progressInterval = setInterval(() => {
          result.progress = Math.min(result.progress + 10, 90)
          setUploadResults(prev => [...prev])
        }, 500)

        // Call real API
        const apiResult = await OpenCartAPI.processPricelist(file)
        
        clearInterval(progressInterval)
        result.progress = 100
        
        const endTime = Date.now()
        result.parseTime = (endTime - startTime) / 1000
        
        if (apiResult.success && apiResult.data) {
          result.status = 'completed'
          result.products = apiResult.data.products || []
          
          toast({
            title: "File processed successfully",
            description: `${file.name} - Found ${result.products.length} products`,
          })
        } else {
          result.status = 'error'
          result.error = apiResult.error || 'Failed to process document'
          
          toast({
            title: "Processing failed",
            description: `Error processing ${file.name}: ${result.error}`,
            variant: "destructive",
          })
        }
        
      } catch (error) {
        result.status = 'error'
        result.error = error instanceof Error ? error.message : 'Unknown error occurred'
        
        toast({
          title: "Processing failed",
          description: `Error processing ${file.name}`,
          variant: "destructive",
        })
      }
      
      setUploadResults(prev => [...prev])
    }
  }, [toast, backendStatus])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFileUpload(files)
    }
  }, [handleFileUpload])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileUpload(files)
    }
  }, [handleFileUpload])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'processing':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
      default:
        return <Clock className="h-4 w-4 text-yellow-500" />
    }
  }

  const getProductStatusBadge = (status: string) => {
    switch (status) {
      case 'valid':
        return <Badge className="bg-green-100 text-green-800">Valid</Badge>
      case 'warning':
        return <Badge className="bg-yellow-100 text-yellow-800">Warning</Badge>
      case 'error':
        return <Badge className="bg-red-100 text-red-800">Error</Badge>
      default:
        return <Badge>Unknown</Badge>
    }
  }

  const getConnectionIcon = () => {
    switch (backendStatus) {
      case 'connected':
        return <Wifi className="h-4 w-4 text-green-500" />
      case 'testing':
        return <RefreshCw className="h-4 w-4 text-yellow-500 animate-spin" />
      default:
        return <WifiOff className="h-4 w-4 text-red-500" />
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
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <FileText className="h-8 w-8 text-blue-500" />
              Pricelist Testing
            </h1>
          </div>
          <div className="flex items-center gap-2">
            {getConnectionIcon()}
            <span className="text-sm font-medium">
              {backendStatus === 'connected' ? 'Backend Connected' : 
               backendStatus === 'testing' ? 'Testing...' : 'Backend Disconnected'}
            </span>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={testBackendConnection}
              disabled={backendStatus === 'testing'}
            >
              Test Connection
            </Button>
          </div>
        </div>
        <p className="text-muted-foreground">
          Upload and test pricelist files with real Document AI parsing
        </p>
      </motion.div>

      {backendStatus === 'disconnected' && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="border-red-200 bg-red-50 dark:bg-red-950/20">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
                <AlertTriangle className="h-4 w-4" />
                <span className="font-medium">Backend Connection Required</span>
              </div>
              <p className="text-sm text-red-600 dark:text-red-300 mt-1">
                Please ensure your Python backend is running on localhost:5000 to process pricelist files with Document AI.
              </p>
            </CardContent>
          </Card>
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload Section */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader>
              <CardTitle>Upload Pricelist Files</CardTitle>
              <CardDescription>
                Drag and drop or select PDF/Excel files to test parsing
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  backendStatus !== 'connected' 
                    ? 'border-gray-200 bg-gray-50 dark:bg-gray-800 opacity-50' 
                    : isDragging 
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-950' 
                      : 'border-gray-300 dark:border-gray-600'
                }`}
                onDrop={backendStatus === 'connected' ? handleDrop : undefined}
                onDragOver={backendStatus === 'connected' ? (e) => e.preventDefault() : undefined}
                onDragEnter={backendStatus === 'connected' ? () => setIsDragging(true) : undefined}
                onDragLeave={backendStatus === 'connected' ? () => setIsDragging(false) : undefined}
              >
                <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-lg font-medium mb-2">
                  {backendStatus === 'connected' 
                    ? 'Drop files here or click to upload' 
                    : 'Backend connection required'}
                </p>
                <p className="text-sm text-muted-foreground mb-4">
                  {backendStatus === 'connected' 
                    ? 'Supports PDF and Excel files up to 10MB'
                    : 'Connect to backend to enable file processing'}
                </p>
                <input
                  type="file"
                  multiple
                  accept=".pdf,.xlsx,.xls"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="file-upload"
                  disabled={backendStatus !== 'connected'}
                />
                <Button asChild disabled={backendStatus !== 'connected'}>
                  <label htmlFor="file-upload" className={backendStatus === 'connected' ? 'cursor-pointer' : 'cursor-not-allowed'}>
                    Select Files
                  </label>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Upload Results */}
          {uploadResults.length > 0 && (
            <Card className="mt-6 bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Processing Results</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {uploadResults.map((result, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(result.status)}
                          <span className="font-medium">{result.fileName}</span>
                        </div>
                        {result.status === 'completed' && (
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setSelectedFile(result)}
                            >
                              <Eye className="h-4 w-4 mr-1" />
                              View
                            </Button>
                            <Button
                              variant="default"
                              size="sm"
                              onClick={() => handleProductComparison(result)}
                              disabled={isComparing}
                            >
                              {isComparing ? (
                                <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
                              ) : (
                                <GitCompare className="h-4 w-4 mr-1" />
                              )}
                              {isComparing ? 'Comparing...' : 'Send to Product Compare'}
                            </Button>
                          </div>
                        )}
                      </div>
                      
                      {result.status === 'processing' && (
                        <Progress value={result.progress} className="mb-2" />
                      )}
                      
                      {result.status === 'completed' && result.products && (
                        <p className="text-sm text-muted-foreground">
                          Found {result.products.length} products • Parsed in {result.parseTime}s
                        </p>
                      )}
                      
                      {result.status === 'error' && (
                        <p className="text-sm text-red-500">{result.error}</p>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </motion.div>

        {/* Results Section */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          {comparisonResult ? (
            <Card className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <GitCompare className="h-5 w-5 text-purple-500" />
                  Product Comparison Results
                </CardTitle>
                <CardDescription>
                  Comparison between parsed products and existing store inventory
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Summary Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <Card className="bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800">
                    <CardContent className="p-4 text-center">
                      <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                        {comparisonResult.summary.addCount}
                      </div>
                      <div className="text-sm text-green-700 dark:text-green-300">To Add</div>
                    </CardContent>
                  </Card>
                  <Card className="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
                    <CardContent className="p-4 text-center">
                      <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                        {comparisonResult.summary.updateCount}
                      </div>
                      <div className="text-sm text-blue-700 dark:text-blue-300">To Update</div>
                    </CardContent>
                  </Card>
                  <Card className="bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800">
                    <CardContent className="p-4 text-center">
                      <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                        {comparisonResult.summary.removeCount}
                      </div>
                      <div className="text-sm text-red-700 dark:text-red-300">To Remove</div>
                    </CardContent>
                  </Card>
                  <Card className="bg-gray-50 dark:bg-gray-950/20 border-gray-200 dark:border-gray-800">
                    <CardContent className="p-4 text-center">
                      <div className="text-2xl font-bold text-gray-600 dark:text-gray-400">
                        {comparisonResult.summary.totalParsed}
                      </div>
                      <div className="text-sm text-gray-700 dark:text-gray-300">Total Parsed</div>
                    </CardContent>
                  </Card>
                </div>

                <Tabs defaultValue="add" className="w-full">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="add">Products to Add ({comparisonResult.summary.addCount})</TabsTrigger>
                    <TabsTrigger value="update">Products to Update ({comparisonResult.summary.updateCount})</TabsTrigger>
                    <TabsTrigger value="remove">Products to Remove ({comparisonResult.summary.removeCount})</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="add" className="space-y-4">
                    <div className="rounded-md border">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Name</TableHead>
                            <TableHead>SKU/Model</TableHead>
                            <TableHead>Price</TableHead>
                            <TableHead>Action</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {comparisonResult.toAdd.map((product) => (
                            <TableRow key={product.id}>
                              <TableCell className="font-medium">{product.name}</TableCell>
                              <TableCell>{product.sku || product.model || '-'}</TableCell>
                              <TableCell>${product.price}</TableCell>
                              <TableCell>
                                <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                                  New Product
                                </Badge>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="update" className="space-y-4">
                    <div className="rounded-md border">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Name</TableHead>
                            <TableHead>SKU/Model</TableHead>
                            <TableHead>Changes</TableHead>
                            <TableHead>Action</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {comparisonResult.toUpdate.map((update, index) => (
                            <TableRow key={index}>
                              <TableCell className="font-medium">{update.parsed.name}</TableCell>
                              <TableCell>{update.parsed.sku || update.parsed.model || '-'}</TableCell>
                              <TableCell>
                                <div className="space-y-1">
                                  {update.differences.map((diff, i) => (
                                    <div key={i} className="text-sm text-muted-foreground">
                                      {diff}
                                    </div>
                                  ))}
                                </div>
                              </TableCell>
                              <TableCell>
                                <Badge className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                                  Update Required
                                </Badge>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="remove" className="space-y-4">
                    <div className="rounded-md border">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Name</TableHead>
                            <TableHead>SKU/Model</TableHead>
                            <TableHead>Price</TableHead>
                            <TableHead>Action</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {comparisonResult.toRemove.map((product) => (
                            <TableRow key={product.id}>
                              <TableCell className="font-medium">{product.name}</TableCell>
                              <TableCell>{product.sku || product.model || '-'}</TableCell>
                              <TableCell>${product.price}</TableCell>
                              <TableCell>
                                <Badge className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                                  Not in Pricelist
                                </Badge>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </TabsContent>
                </Tabs>

                <div className="mt-6 flex gap-2">
                  <Button 
                    variant="outline" 
                    onClick={() => setComparisonResult(null)}
                  >
                    Close Comparison
                  </Button>
                  <Button 
                    variant="default"
                    disabled
                    className="opacity-50"
                  >
                    Apply Changes (Coming Soon)
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : selectedFile ? (
            <Card className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  Parsed Products
                  <Button variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-1" />
                    Export
                  </Button>
                </CardTitle>
                <CardDescription>
                  Results from {selectedFile.fileName}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="products" className="w-full">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="products">Products</TabsTrigger>
                    <TabsTrigger value="issues">Issues</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="products" className="space-y-4">
                    <div className="rounded-md border">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Name</TableHead>
                            <TableHead>SKU</TableHead>
                            <TableHead>Price</TableHead>
                            <TableHead>Status</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {selectedFile.products?.map((product) => (
                            <TableRow key={product.id}>
                              <TableCell className="font-medium">
                                {product.name}
                              </TableCell>
                              <TableCell>{product.sku || '-'}</TableCell>
                              <TableCell>
                                {product.price > 0 ? `$${product.price}` : '-'}
                              </TableCell>
                              <TableCell>
                                {getProductStatusBadge(product.status)}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="issues" className="space-y-4">
                    {selectedFile.products?.filter(p => p.issues?.length).map((product) => (
                      <div key={product.id} className="border rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <AlertTriangle className="h-4 w-4 text-yellow-500" />
                          <span className="font-medium">{product.name}</span>
                        </div>
                        <ul className="text-sm text-muted-foreground space-y-1">
                          {product.issues?.map((issue, index) => (
                            <li key={index}>• {issue}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          ) : (
            <Card className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-0 shadow-lg">
              <CardContent className="flex items-center justify-center h-64">
                <div className="text-center">
                  <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-lg font-medium mb-2">
                    {backendStatus === 'connected' ? 'No file selected' : 'Backend not connected'}
                  </p>
                  <p className="text-muted-foreground">
                    {backendStatus === 'connected' 
                      ? 'Upload a file and click "View" to see parsed results or "Send to Product Compare" to analyze differences'
                      : 'Connect to backend to start processing pricelist files'
                    }
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </motion.div>
      </div>
    </div>
  )
}
