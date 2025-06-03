
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
  Minus
} from 'lucide-react'

interface ComparisonResult {
  id: string
  parsedProduct: {
    name: string
    sku: string
    price: number
    description: string
  }
  existingProduct?: {
    name: string
    sku: string
    price: number
    description: string
    id: string
  }
  matchType: 'exact' | 'similar' | 'none'
  similarity: number
  action: 'create' | 'update' | 'skip'
  priceChange?: number
  issues: string[]
}

export default function ProductComparison() {
  const [comparisonResults, setComparisonResults] = useState<ComparisonResult[]>([])
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisProgress, setAnalysisProgress] = useState(0)
  const [selectedFile, setSelectedFile] = useState('')
  const [filterAction, setFilterAction] = useState<string>('all')
  const { toast } = useToast()

  // Mock comparison data
  const mockResults: ComparisonResult[] = [
    {
      id: '1',
      parsedProduct: {
        name: 'Professional Audio Mixer XM-2000',
        sku: 'AUD-XM-2000',
        price: 2599.99,
        description: 'High-quality professional audio mixer with 24 channels'
      },
      existingProduct: {
        name: 'Professional Audio Mixer XM-2000',
        sku: 'AUD-XM-2000',
        price: 2499.99,
        description: 'High-quality professional audio mixer with 24 channels',
        id: 'existing-1'
      },
      matchType: 'exact',
      similarity: 100,
      action: 'update',
      priceChange: 100,
      issues: []
    },
    {
      id: '2',
      parsedProduct: {
        name: 'Studio Monitor Speakers SM-150 Pro',
        sku: 'AUD-SM-150-PRO',
        price: 949.99,
        description: 'Professional studio monitor speakers with enhanced bass'
      },
      existingProduct: {
        name: 'Studio Monitor Speakers SM-150',
        sku: 'AUD-SM-150',
        price: 899.99,
        description: 'Professional studio monitor speakers',
        id: 'existing-2'
      },
      matchType: 'similar',
      similarity: 85,
      action: 'update',
      priceChange: 50,
      issues: ['SKU mismatch', 'Description differs']
    },
    {
      id: '3',
      parsedProduct: {
        name: 'Wireless Headset WH-500',
        sku: 'AUD-WH-500',
        price: 299.99,
        description: 'Professional wireless headset for studio use'
      },
      matchType: 'none',
      similarity: 0,
      action: 'create',
      issues: []
    },
    {
      id: '4',
      parsedProduct: {
        name: 'Audio Interface AI-200',
        sku: 'AUD-AI-200',
        price: 0,
        description: ''
      },
      matchType: 'none',
      similarity: 0,
      action: 'skip',
      issues: ['Invalid price', 'Missing description']
    }
  ]

  const runComparison = async () => {
    setIsAnalyzing(true)
    setAnalysisProgress(0)
    
    // Simulate analysis progress
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(resolve => setTimeout(resolve, 200))
      setAnalysisProgress(i)
    }
    
    setComparisonResults(mockResults)
    setIsAnalyzing(false)
    
    toast({
      title: "Analysis complete",
      description: `Found ${mockResults.length} products to analyze`,
    })
  }

  const filteredResults = comparisonResults.filter(result => 
    filterAction === 'all' || result.action === filterAction
  )

  const getMatchBadge = (matchType: string, similarity: number) => {
    switch (matchType) {
      case 'exact':
        return <Badge className="bg-green-100 text-green-800">Exact Match</Badge>
      case 'similar':
        return <Badge className="bg-yellow-100 text-yellow-800">Similar ({similarity}%)</Badge>
      case 'none':
        return <Badge className="bg-gray-100 text-gray-800">No Match</Badge>
      default:
        return <Badge>Unknown</Badge>
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

  const stats = {
    total: comparisonResults.length,
    create: comparisonResults.filter(r => r.action === 'create').length,
    update: comparisonResults.filter(r => r.action === 'update').length,
    skip: comparisonResults.filter(r => r.action === 'skip').length,
    issues: comparisonResults.filter(r => r.issues.length > 0).length
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
            <CardTitle>Run Product Comparison</CardTitle>
            <CardDescription>
              Analyze parsed products against existing store inventory
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <Label htmlFor="file-select">Select Parsed File</Label>
                <Input
                  id="file-select"
                  value={selectedFile}
                  onChange={(e) => setSelectedFile(e.target.value)}
                  placeholder="pricelist_2024_05_28.pdf"
                />
              </div>
              <Button 
                onClick={runComparison} 
                disabled={isAnalyzing}
                className="mt-6"
              >
                {isAnalyzing ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <GitCompare className="h-4 w-4 mr-2" />
                    Run Analysis
                  </>
                )}
              </Button>
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
          className="grid grid-cols-1 md:grid-cols-5 gap-4"
        >
          <Card className="bg-gradient-to-br from-blue-500 to-cyan-500 text-white border-0 shadow-lg">
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-blue-100 text-sm">Total Products</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-green-500 to-emerald-500 text-white border-0 shadow-lg">
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-green-100 text-sm">Create New</p>
                <p className="text-2xl font-bold">{stats.create}</p>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-orange-500 to-red-500 text-white border-0 shadow-lg">
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-orange-100 text-sm">Update Existing</p>
                <p className="text-2xl font-bold">{stats.update}</p>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-gray-500 to-slate-500 text-white border-0 shadow-lg">
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-gray-100 text-sm">Skip</p>
                <p className="text-2xl font-bold">{stats.skip}</p>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-yellow-500 to-amber-500 text-white border-0 shadow-lg">
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-yellow-100 text-sm">Issues</p>
                <p className="text-2xl font-bold">{stats.issues}</p>
              </div>
            </CardContent>
          </Card>
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
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium">{result.parsedProduct.name}</h3>
                        {getMatchBadge(result.matchType, result.similarity)}
                        {getActionBadge(result.action)}
                      </div>
                      {result.issues.length > 0 && (
                        <AlertTriangle className="h-5 w-5 text-yellow-500" />
                      )}
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Parsed Product */}
                      <div className="space-y-2">
                        <h4 className="text-sm font-medium text-blue-600">Parsed Data</h4>
                        <div className="text-sm space-y-1">
                          <p><span className="text-muted-foreground">SKU:</span> {result.parsedProduct.sku}</p>
                          <p><span className="text-muted-foreground">Price:</span> R{result.parsedProduct.price}</p>
                          <p><span className="text-muted-foreground">Description:</span> {result.parsedProduct.description || 'N/A'}</p>
                        </div>
                      </div>
                      
                      {/* Existing Product */}
                      {result.existingProduct && (
                        <>
                          <div className="space-y-2">
                            <h4 className="text-sm font-medium text-green-600">Existing Product</h4>
                            <div className="text-sm space-y-1">
                              <p><span className="text-muted-foreground">SKU:</span> {result.existingProduct.sku}</p>
                              <p className="flex items-center gap-2">
                                <span className="text-muted-foreground">Price:</span> 
                                R{result.existingProduct.price}
                                {result.priceChange && (
                                  <div className="flex items-center gap-1">
                                    <ArrowRight className="h-3 w-3" />
                                    <span className={result.priceChange > 0 ? 'text-green-600' : 'text-red-600'}>
                                      R{result.parsedProduct.price}
                                    </span>
                                    {getPriceChangeIcon(result.priceChange)}
                                  </div>
                                )}
                              </p>
                              <p><span className="text-muted-foreground">Description:</span> {result.existingProduct.description}</p>
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                    
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
