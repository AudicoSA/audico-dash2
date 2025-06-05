
'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Progress } from '@/components/ui/progress'
import { useToast } from '@/hooks/use-toast'
import { Textarea } from '@/components/ui/textarea'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { 
  GitCompare, 
  Search, 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Minus,
  ChevronDown,
  ChevronRight,
  Database,
  Bug,
  Upload
} from 'lucide-react'

interface ComparisonResult {
  id: string
  parsedProduct: {
    name: string
    sku: string
    price: number
    description: string
    model: string
  }
  existingProduct?: {
    name: string
    sku: string
    price: number
    description: string
    id: string
    model: string
  }
  matchType: string
  similarity: number
  action: 'create' | 'update' | 'skip'
  priceChange?: number
  issues: string[]
  confidenceLevel: string
  debugInfo?: any
}

interface ComparisonSummary {
  total_products: number
  actions: {
    create: number
    update: number
    skip: number
  }
  match_types: {
    exact_sku: number
    exact_model: number
    fuzzy_name: number
    model_extracted: number
    partial_match: number
    no_match: number
  }
  confidence_levels: {
    high: number
    medium: number
    low: number
    none: number
  }
  issues_count: number
  products_with_issues: number
  average_confidence: number
}

export default function ProductComparison() {
  const [comparisonResults, setComparisonResults] = useState<ComparisonResult[]>([])
  const [comparisonSummary, setComparisonSummary] = useState<ComparisonSummary | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisProgress, setAnalysisProgress] = useState(0)
  const [selectedFile, setSelectedFile] = useState('')
  const [testData, setTestData] = useState('')
  const [filterAction, setFilterAction] = useState<string>('all')
  const [showDebugInfo, setShowDebugInfo] = useState(false)
  const [existingProductsCount, setExistingProductsCount] = useState(0)
  const { toast } = useToast()

  // Sample Denon pricelist data for testing
  const sampleDenonData = `AVR-S540H    Denon AVR-S540H 5.2 Channel AV Receiver R 8,999.00
AVR-S750H       Denon AVR-S750H 7.2 Channel AV Receiver R 12,999.00
AVR-X1800H      Denon AVR-X1800H 7.2 Channel AV Receiver        R 18,999.00
AVR-X2800H      Denon AVR-X2800H 7.2 Channel AV Receiver        R 24,999.00
AVR-X3800H      Denon AVR-X3800H 9.2 Channel AV Receiver        R 34,999.00
PMA-600NE       Denon PMA-600NE Integrated Amplifier    R 12,999.00
DCD-600NE       Denon DCD-600NE CD Player       R 8,999.00`

  const runComparison = async () => {
    if (!testData.trim()) {
      toast({
        title: "No data to compare",
        description: "Please enter some test data or use the sample data",
        variant: "destructive"
      })
      return
    }

    setIsAnalyzing(true)
    setAnalysisProgress(0)
    
    try {
      // Step 1: Parse the test data into products
      setAnalysisProgress(20)
      const products = parseTestData(testData)
      
      if (products.length === 0) {
        throw new Error("No valid products found in test data")
      }

      // Step 2: Call the comparison API
      setAnalysisProgress(50)
      const response = await fetch('http://localhost:5000/api/products/compare', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          products: products
        })
      })

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`)
      }

      const data = await response.json()
      setAnalysisProgress(80)

      if (!data.success) {
        throw new Error(data.message || 'Comparison failed')
      }

      // Step 3: Process results
      setComparisonResults(data.data.results || [])
      setComparisonSummary(data.data.summary || null)
      setExistingProductsCount(data.data.existing_products_count || 0)
      setAnalysisProgress(100)

      toast({
        title: "Analysis complete",
        description: `Compared ${products.length} products against ${data.data.existing_products_count || 0} existing products`,
      })

    } catch (error) {
      console.error('Comparison error:', error)
      toast({
        title: "Analysis failed",
        description: error instanceof Error ? error.message : "Unknown error occurred",
        variant: "destructive"
      })
    } finally {
      setIsAnalyzing(false)
    }
  }

  const parseTestData = (data: string) => {
    const lines = data.trim().split('\n')
    const products = []

    for (const line of lines) {
      if (!line.trim()) continue
      
      // Try to parse tab-separated format: MODEL\tNAME\tPRICE
      const parts = line.split('\t')
      if (parts.length >= 3) {
        const model = parts[0].trim()
        const name = parts[1].trim()
        const priceStr = parts[2].trim()
        
        // Extract price number
        const priceMatch = priceStr.match(/[\d,]+\.?\d*/);
        const price = priceMatch ? parseFloat(priceMatch[0].replace(/,/g, '')) : 0

        if (model && name && price > 0) {
          products.push({
            name: name,
            model: model,
            sku: model,
            price: price,
            description: name,
            category: 'Audio Equipment',
            manufacturer: 'Denon'
          })
        }
      }
    }

    return products
  }

  const reloadExistingProducts = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/products/reload-existing', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })

      const data = await response.json()
      
      if (data.success) {
        setExistingProductsCount(data.products_count || 0)
        toast({
          title: "Products reloaded",
          description: `Successfully reloaded ${data.products_count || 0} existing products`,
        })
      } else {
        throw new Error(data.message || 'Failed to reload products')
      }
    } catch (error) {
      console.error('Reload error:', error)
      toast({
        title: "Reload failed",
        description: error instanceof Error ? error.message : "Unknown error occurred",
        variant: "destructive"
      })
    }
  }

  const filteredResults = comparisonResults.filter(result => 
    filterAction === 'all' || result.action === filterAction
  )

  const getMatchBadge = (matchType: string, similarity: number) => {
    switch (matchType) {
      case 'exact_sku':
        return <Badge className="bg-green-100 text-green-800">Exact SKU</Badge>
      case 'exact_model':
        return <Badge className="bg-green-100 text-green-800">Exact Model</Badge>
      case 'model_extracted':
        return <Badge className="bg-blue-100 text-blue-800">Model Match</Badge>
      case 'fuzzy_name':
        return <Badge className="bg-yellow-100 text-yellow-800">Fuzzy Name ({similarity}%)</Badge>
      case 'partial_match':
        return <Badge className="bg-orange-100 text-orange-800">Partial ({similarity}%)</Badge>
      case 'no_match':
        return <Badge className="bg-gray-100 text-gray-800">No Match</Badge>
      default:
        return <Badge className="bg-gray-100 text-gray-800">{matchType}</Badge>
    }
  }

  const getConfidenceBadge = (confidenceLevel: string) => {
    switch (confidenceLevel) {
      case 'high':
        return <Badge className="bg-green-100 text-green-800">High</Badge>
      case 'medium':
        return <Badge className="bg-yellow-100 text-yellow-800">Medium</Badge>
      case 'low':
        return <Badge className="bg-orange-100 text-orange-800">Low</Badge>
      case 'none':
        return <Badge className="bg-red-100 text-red-800">None</Badge>
      default:
        return <Badge className="bg-gray-100 text-gray-800">{confidenceLevel}</Badge>
    }
  }

  const getActionBadge = (action: string) => {
    switch (action) {
      case 'create':
        return <Badge className="bg-blue-100 text-blue-800">Create New</Badge>
      case 'update':
        return <Badge className="bg-orange-100 text-orange-800">Update Existing</Badge>
      case 'skip':
        return <Badge className="bg-gray-100 text-gray-800">Skip</Badge>
      default:
        return <Badge>Unknown</Badge>
    }
  }

  const getPriceChangeIcon = (change?: number) => {
    if (!change) return <Minus className="h-4 w-4 text-gray-400" />
    if (change > 0) return <TrendingUp className="h-4 w-4 text-green-500" />
    return <TrendingDown className="h-4 w-4 text-red-500" />
  }

  const stats = comparisonSummary || {
    total_products: comparisonResults.length,
    actions: {
      create: comparisonResults.filter(r => r.action === 'create').length,
      update: comparisonResults.filter(r => r.action === 'update').length,
      skip: comparisonResults.filter(r => r.action === 'skip').length,
    },
    confidence_levels: {
      high: comparisonResults.filter(r => r.confidenceLevel === 'high').length,
      medium: comparisonResults.filter(r => r.confidenceLevel === 'medium').length,
      low: comparisonResults.filter(r => r.confidenceLevel === 'low').length,
      none: comparisonResults.filter(r => r.confidenceLevel === 'none').length,
    },
    issues_count: comparisonResults.reduce((sum, r) => sum + r.issues.length, 0),
    products_with_issues: comparisonResults.filter(r => r.issues.length > 0).length,
    average_confidence: comparisonResults.length > 0 
      ? comparisonResults.reduce((sum, r) => sum + r.similarity, 0) / comparisonResults.length 
      : 0
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
          <GitCompare className="h-8 w-8 text-purple-500" />
          Product Comparison
        </h1>
        <p className="text-muted-foreground">
          Compare parsed pricelist data with existing store products
        </p>
      </motion.div>

      {/* Analysis Controls */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-0 shadow-lg">
          <CardHeader>
            <CardTitle>Product Comparison Analysis</CardTitle>
            <CardDescription>
              Test the enhanced product matching logic with sample Denon data
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="test-data">Test Data (Tab-separated: Model, Name, Price)</Label>
                <Textarea
                  id="test-data"
                  value={testData}
                  onChange={(e) => setTestData(e.target.value)}
                  placeholder="Enter product data..."
                  rows={6}
                />
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setTestData(sampleDenonData)}
                >
                  <Upload className="h-4 w-4 mr-2" />
                  Load Sample Denon Data
                </Button>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">Existing Products</h4>
                    <p className="text-sm text-muted-foreground">
                      {existingProductsCount} products loaded from OpenCart
                    </p>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={reloadExistingProducts}
                  >
                    <Database className="h-4 w-4 mr-2" />
                    Reload
                  </Button>
                </div>
                
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="debug-info"
                    checked={showDebugInfo}
                    onChange={(e) => setShowDebugInfo(e.target.checked)}
                    className="rounded"
                  />
                  <Label htmlFor="debug-info" className="text-sm">
                    Show debug information
                  </Label>
                </div>
                
                <Button 
                  onClick={runComparison} 
                  disabled={isAnalyzing || !testData.trim()}
                  className="w-full"
                >
                  {isAnalyzing ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <GitCompare className="h-4 w-4 mr-2" />
                      Run Comparison Analysis
                    </>
                  )}
                </Button>
              </div>
            </div>
            
            {isAnalyzing && (
              <div className="mt-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-muted-foreground">Analysis Progress</span>
                  <span className="text-sm font-medium">{analysisProgress}%</span>
                </div>
                <Progress value={analysisProgress} />
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Stats */}
      {comparisonResults.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="space-y-4"
        >
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <Card className="bg-gradient-to-br from-blue-500 to-cyan-500 text-white border-0 shadow-lg">
              <CardContent className="p-4">
                <div className="text-center">
                  <p className="text-blue-100 text-sm">Total Products</p>
                  <p className="text-2xl font-bold">{stats.total_products}</p>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-gradient-to-br from-green-500 to-emerald-500 text-white border-0 shadow-lg">
              <CardContent className="p-4">
                <div className="text-center">
                  <p className="text-green-100 text-sm">Create New</p>
                  <p className="text-2xl font-bold">{stats.actions.create}</p>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-gradient-to-br from-orange-500 to-red-500 text-white border-0 shadow-lg">
              <CardContent className="p-4">
                <div className="text-center">
                  <p className="text-orange-100 text-sm">Update Existing</p>
                  <p className="text-2xl font-bold">{stats.actions.update}</p>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-gradient-to-br from-gray-500 to-slate-500 text-white border-0 shadow-lg">
              <CardContent className="p-4">
                <div className="text-center">
                  <p className="text-gray-100 text-sm">Skip</p>
                  <p className="text-2xl font-bold">{stats.actions.skip}</p>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-gradient-to-br from-yellow-500 to-amber-500 text-white border-0 shadow-lg">
              <CardContent className="p-4">
                <div className="text-center">
                  <p className="text-yellow-100 text-sm">Issues</p>
                  <p className="text-2xl font-bold">{stats.products_with_issues}</p>
                </div>
              </CardContent>
            </Card>
          </div>
          
          {/* Additional Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-gradient-to-br from-purple-500 to-indigo-500 text-white border-0 shadow-lg">
              <CardContent className="p-4">
                <div className="text-center">
                  <p className="text-purple-100 text-sm">High Confidence</p>
                  <p className="text-2xl font-bold">{stats.confidence_levels.high}</p>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-gradient-to-br from-teal-500 to-cyan-500 text-white border-0 shadow-lg">
              <CardContent className="p-4">
                <div className="text-center">
                  <p className="text-teal-100 text-sm">Medium Confidence</p>
                  <p className="text-2xl font-bold">{stats.confidence_levels.medium}</p>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-gradient-to-br from-pink-500 to-rose-500 text-white border-0 shadow-lg">
              <CardContent className="p-4">
                <div className="text-center">
                  <p className="text-pink-100 text-sm">Low Confidence</p>
                  <p className="text-2xl font-bold">{stats.confidence_levels.low}</p>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-gradient-to-br from-slate-600 to-gray-600 text-white border-0 shadow-lg">
              <CardContent className="p-4">
                <div className="text-center">
                  <p className="text-slate-100 text-sm">Avg Confidence</p>
                  <p className="text-2xl font-bold">{Math.round(stats.average_confidence)}%</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </motion.div>
      )}

      {/* Results */}
      {comparisonResults.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Comparison Results
                <div className="flex gap-2">
                  <Button
                    variant={filterAction === 'all' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setFilterAction('all')}
                  >
                    All
                  </Button>
                  <Button
                    variant={filterAction === 'create' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setFilterAction('create')}
                  >
                    Create
                  </Button>
                  <Button
                    variant={filterAction === 'update' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setFilterAction('update')}
                  >
                    Update
                  </Button>
                  <Button
                    variant={filterAction === 'skip' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setFilterAction('skip')}
                  >
                    Skip
                  </Button>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredResults.map((result) => (
                  <div key={result.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-medium">{result.parsedProduct.name}</h3>
                        {getMatchBadge(result.matchType, result.similarity)}
                        {getConfidenceBadge(result.confidenceLevel)}
                        {getActionBadge(result.action)}
                      </div>
                      <div className="flex items-center gap-2">
                        {result.issues.length > 0 && (
                          <AlertTriangle className="h-5 w-5 text-yellow-500" />
                        )}
                        {showDebugInfo && result.debugInfo && (
                          <Bug className="h-5 w-5 text-blue-500" />
                        )}
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Parsed Product */}
                      <div className="space-y-2">
                        <h4 className="text-sm font-medium text-blue-600">Parsed Data</h4>
                        <div className="text-sm space-y-1">
                          <p><span className="text-muted-foreground">Model:</span> {result.parsedProduct.model}</p>
                          <p><span className="text-muted-foreground">SKU:</span> {result.parsedProduct.sku}</p>
                          <p><span className="text-muted-foreground">Price:</span> R{result.parsedProduct.price.toLocaleString()}</p>
                          <p><span className="text-muted-foreground">Description:</span> {result.parsedProduct.description || 'N/A'}</p>
                        </div>
                      </div>
                      
                      {/* Existing Product */}
                      {result.existingProduct ? (
                        <div className="space-y-2">
                          <h4 className="text-sm font-medium text-green-600">Existing Product (ID: {result.existingProduct.id})</h4>
                          <div className="text-sm space-y-1">
                            <p><span className="text-muted-foreground">Model:</span> {result.existingProduct.model}</p>
                            <p><span className="text-muted-foreground">SKU:</span> {result.existingProduct.sku}</p>
                            <p className="flex items-center gap-2">
                              <span className="text-muted-foreground">Price:</span> 
                              R{parseFloat(result.existingProduct.price.toString()).toLocaleString()}
                              {result.priceChange && (
                                <div className="flex items-center gap-1">
                                  <ArrowRight className="h-3 w-3" />
                                  <span className={result.priceChange > 0 ? 'text-green-600' : 'text-red-600'}>
                                    R{result.parsedProduct.price.toLocaleString()}
                                  </span>
                                  {getPriceChangeIcon(result.priceChange)}
                                  <span className="text-xs text-muted-foreground">
                                    ({result.priceChange > 0 ? '+' : ''}R{Math.abs(result.priceChange).toLocaleString()})
                                  </span>
                                </div>
                              )}
                            </p>
                            <p><span className="text-muted-foreground">Description:</span> {result.existingProduct.description}</p>
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          <h4 className="text-sm font-medium text-gray-600">No Existing Product Found</h4>
                          <p className="text-sm text-muted-foreground">
                            This product will be created as new in OpenCart.
                          </p>
                        </div>
                      )}
                    </div>
                    
                    {/* Debug Information */}
                    {showDebugInfo && result.debugInfo && (
                      <Collapsible className="mt-3">
                        <CollapsibleTrigger className="flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-800">
                          <ChevronRight className="h-4 w-4" />
                          Debug Information
                        </CollapsibleTrigger>
                        <CollapsibleContent className="mt-2 p-3 bg-blue-50 dark:bg-blue-950 rounded-lg">
                          <div className="text-sm space-y-2">
                            <p><span className="font-medium">Products Checked:</span> {result.debugInfo.total_products_checked}</p>
                            <p><span className="font-medium">Best Score:</span> {(result.debugInfo.best_score * 100).toFixed(1)}%</p>
                            {result.debugInfo.model_extraction && (
                              <div>
                                <span className="font-medium">Model Extraction:</span>
                                <ul className="ml-4 mt-1">
                                  <li>Parsed: {result.debugInfo.model_extraction.parsed || 'None'}</li>
                                  <li>Existing: {result.debugInfo.model_extraction.existing || 'None'}</li>
                                </ul>
                              </div>
                            )}
                          </div>
                        </CollapsibleContent>
                      </Collapsible>
                    )}
                    
                    {result.issues.length > 0 && (
                      <div className="mt-3 p-3 bg-yellow-50 dark:bg-yellow-950 rounded-lg">
                        <h4 className="text-sm font-medium text-yellow-800 dark:text-yellow-200 mb-1">Issues Found:</h4>
                        <ul className="text-sm text-yellow-700 dark:text-yellow-300 space-y-1">
                          {result.issues.map((issue, index) => (
                            <li key={index}>• {issue}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Empty State */}
      {comparisonResults.length === 0 && !isAnalyzing && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-0 shadow-lg">
            <CardContent className="flex items-center justify-center h-64">
              <div className="text-center">
                <GitCompare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-lg font-medium mb-2">No comparison results</p>
                <p className="text-muted-foreground">
                  Run a product comparison analysis to see results
                </p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  )
}
