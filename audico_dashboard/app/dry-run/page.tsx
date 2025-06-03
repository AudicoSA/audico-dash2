
'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useToast } from '@/hooks/use-toast'
import { 
  PlayCircle, 
  FileText, 
  Plus, 
  Edit, 
  Trash2, 
  CheckCircle, 
  XCircle, 
  Clock,
  Download,
  RefreshCw,
  AlertTriangle,
  TrendingUp,
  TrendingDown
} from 'lucide-react'

interface DryRunResult {
  id: string
  action: 'create' | 'update' | 'delete' | 'skip'
  product: {
    name: string
    sku: string
    price: number
    category: string
  }
  existingProduct?: {
    name: string
    sku: string
    price: number
  }
  changes?: {
    field: string
    oldValue: any
    newValue: any
  }[]
  issues: string[]
  impact: 'low' | 'medium' | 'high'
}

interface DryRunSummary {
  totalProducts: number
  actions: {
    create: number
    update: number
    delete: number
    skip: number
  }
  estimatedTime: string
  potentialIssues: number
}

export default function DryRunOperations() {
  const [isRunning, setIsRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [results, setResults] = useState<DryRunResult[]>([])
  const [summary, setSummary] = useState<DryRunSummary | null>(null)
  const [selectedFiles, setSelectedFiles] = useState<string[]>([])
  const [filterAction, setFilterAction] = useState<string>('all')
  const { toast } = useToast()

  // Mock available files
  const availableFiles = [
    'pricelist_2024_05_28.pdf',
    'pricelist_2024_05_27.xlsx',
    'inventory_update_2024_05_26.pdf'
  ]

  // Mock dry run results
  const mockResults: DryRunResult[] = [
    {
      id: '1',
      action: 'update',
      product: {
        name: 'Professional Audio Mixer XM-2000',
        sku: 'AUD-XM-2000',
        price: 2599.99,
        category: 'Audio Equipment'
      },
      existingProduct: {
        name: 'Professional Audio Mixer XM-2000',
        sku: 'AUD-XM-2000',
        price: 2499.99
      },
      changes: [
        { field: 'price', oldValue: 2499.99, newValue: 2599.99 }
      ],
      issues: [],
      impact: 'medium'
    },
    {
      id: '2',
      action: 'create',
      product: {
        name: 'Wireless Headset WH-500',
        sku: 'AUD-WH-500',
        price: 299.99,
        category: 'Headphones'
      },
      issues: [],
      impact: 'low'
    },
    {
      id: '3',
      action: 'update',
      product: {
        name: 'Studio Monitor Speakers SM-150',
        sku: 'AUD-SM-150',
        price: 949.99,
        category: 'Speakers'
      },
      existingProduct: {
        name: 'Studio Monitor Speakers SM-150',
        sku: 'AUD-SM-150',
        price: 899.99
      },
      changes: [
        { field: 'price', oldValue: 899.99, newValue: 949.99 }
      ],
      issues: ['Significant price increase'],
      impact: 'high'
    },
    {
      id: '4',
      action: 'skip',
      product: {
        name: 'Invalid Product',
        sku: '',
        price: 0,
        category: 'Unknown'
      },
      issues: ['Missing SKU', 'Invalid price', 'Unknown category'],
      impact: 'low'
    }
  ]

  const runDryRun = async () => {
    if (selectedFiles.length === 0) {
      toast({
        title: "No files selected",
        description: "Please select at least one file to process",
        variant: "destructive"
      })
      return
    }

    setIsRunning(true)
    setProgress(0)
    setResults([])
    setSummary(null)

    // Simulate progress
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(resolve => setTimeout(resolve, 300))
      setProgress(i)
    }

    // Set results
    setResults(mockResults)
    setSummary({
      totalProducts: mockResults.length,
      actions: {
        create: mockResults.filter(r => r.action === 'create').length,
        update: mockResults.filter(r => r.action === 'update').length,
        delete: mockResults.filter(r => r.action === 'delete').length,
        skip: mockResults.filter(r => r.action === 'skip').length
      },
      estimatedTime: '2.5 minutes',
      potentialIssues: mockResults.filter(r => r.issues.length > 0).length
    })

    setIsRunning(false)

    toast({
      title: "Dry run completed",
      description: `Analyzed ${mockResults.length} products`,
    })
  }

  const handleFileSelection = (fileName: string, checked: boolean) => {
    if (checked) {
      setSelectedFiles(prev => [...prev, fileName])
    } else {
      setSelectedFiles(prev => prev.filter(f => f !== fileName))
    }
  }

  const filteredResults = results.filter(result => 
    filterAction === 'all' || result.action === filterAction
  )

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'create':
        return <Plus className="h-4 w-4 text-blue-500" />
      case 'update':
        return <Edit className="h-4 w-4 text-orange-500" />
      case 'delete':
        return <Trash2 className="h-4 w-4 text-red-500" />
      case 'skip':
        return <XCircle className="h-4 w-4 text-gray-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-500" />
    }
  }

  const getActionBadge = (action: string) => {
    switch (action) {
      case 'create':
        return <Badge className="bg-blue-100 text-blue-800">Create</Badge>
      case 'update':
        return <Badge className="bg-orange-100 text-orange-800">Update</Badge>
      case 'delete':
        return <Badge className="bg-red-100 text-red-800">Delete</Badge>
      case 'skip':
        return <Badge className="bg-gray-100 text-gray-800">Skip</Badge>
      default:
        return <Badge>Unknown</Badge>
    }
  }

  const getImpactBadge = (impact: string) => {
    switch (impact) {
      case 'high':
        return <Badge className="bg-red-100 text-red-800">High Impact</Badge>
      case 'medium':
        return <Badge className="bg-yellow-100 text-yellow-800">Medium Impact</Badge>
      case 'low':
        return <Badge className="bg-green-100 text-green-800">Low Impact</Badge>
      default:
        return <Badge>Unknown</Badge>
    }
  }

  const getPriceChangeIcon = (oldPrice: number, newPrice: number) => {
    if (newPrice > oldPrice) {
      return <TrendingUp className="h-4 w-4 text-green-500" />
    } else if (newPrice < oldPrice) {
      return <TrendingDown className="h-4 w-4 text-red-500" />
    }
    return null
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
          <PlayCircle className="h-8 w-8 text-indigo-500" />
          Dry Run Operations
        </h1>
        <p className="text-muted-foreground">
          Run safe operations without making actual changes to analyze potential impacts
        </p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader>
              <CardTitle>Dry Run Configuration</CardTitle>
              <CardDescription>
                Select files and configure dry run parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Select Files to Process</Label>
                <div className="space-y-2">
                  {availableFiles.map((file) => (
                    <div key={file} className="flex items-center space-x-2">
                      <Checkbox
                        id={file}
                        checked={selectedFiles.includes(file)}
                        onCheckedChange={(checked) => handleFileSelection(file, checked as boolean)}
                      />
                      <Label htmlFor={file} className="text-sm font-normal">
                        {file}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="batch-size">Batch Size</Label>
                <Input id="batch-size" type="number" defaultValue="50" />
              </div>

              <div className="space-y-2">
                <Label htmlFor="similarity-threshold">Similarity Threshold (%)</Label>
                <Input id="similarity-threshold" type="number" defaultValue="80" />
              </div>

              <Button 
                onClick={runDryRun} 
                disabled={isRunning || selectedFiles.length === 0}
                className="w-full"
              >
                {isRunning ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Running Analysis...
                  </>
                ) : (
                  <>
                    <PlayCircle className="h-4 w-4 mr-2" />
                    Start Dry Run
                  </>
                )}
              </Button>

              {isRunning && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Progress</span>
                    <span className="text-sm font-medium">{progress}%</span>
                  </div>
                  <Progress value={progress} />
                </div>
              )}
            </CardContent>
          </Card>

          {/* Summary */}
          {summary && (
            <Card className="mt-6 bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Analysis Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Total Products:</span>
                  <span className="font-medium">{summary.totalProducts}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Create:</span>
                  <span className="font-medium text-blue-600">{summary.actions.create}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Update:</span>
                  <span className="font-medium text-orange-600">{summary.actions.update}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Skip:</span>
                  <span className="font-medium text-gray-600">{summary.actions.skip}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Est. Time:</span>
                  <span className="font-medium">{summary.estimatedTime}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Issues:</span>
                  <span className="font-medium text-red-600">{summary.potentialIssues}</span>
                </div>
              </CardContent>
            </Card>
          )}
        </motion.div>

        {/* Results */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-2"
        >
          <Card className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Dry Run Results
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
                    Issues
                  </Button>
                  {results.length > 0 && (
                    <Button variant="outline" size="sm">
                      <Download className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </CardTitle>
              <CardDescription>
                Preview of changes that would be made during actual execution
              </CardDescription>
            </CardHeader>
            <CardContent>
              {results.length > 0 ? (
                <ScrollArea className="h-96">
                  <div className="space-y-4">
                    {filteredResults.map((result) => (
                      <div key={result.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            {getActionIcon(result.action)}
                            <h3 className="font-medium">{result.product.name}</h3>
                            {getActionBadge(result.action)}
                            {getImpactBadge(result.impact)}
                          </div>
                          {result.issues.length > 0 && (
                            <AlertTriangle className="h-5 w-5 text-yellow-500" />
                          )}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                          <div className="space-y-1">
                            <p className="text-sm"><span className="text-muted-foreground">SKU:</span> {result.product.sku || 'N/A'}</p>
                            <p className="text-sm"><span className="text-muted-foreground">Price:</span> ${result.product.price}</p>
                            <p className="text-sm"><span className="text-muted-foreground">Category:</span> {result.product.category}</p>
                          </div>

                          {result.existingProduct && (
                            <div className="space-y-1">
                              <p className="text-sm text-muted-foreground">Current Values:</p>
                              <p className="text-sm">Price: ${result.existingProduct.price}</p>
                              {result.changes && result.changes.map((change, index) => (
                                <div key={index} className="flex items-center gap-2 text-sm">
                                  <span>{change.field}: ${change.oldValue} → ${change.newValue}</span>
                                  {change.field === 'price' && getPriceChangeIcon(change.oldValue, change.newValue)}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>

                        {result.issues.length > 0 && (
                          <div className="bg-yellow-50 dark:bg-yellow-950 p-3 rounded-lg">
                            <h4 className="text-sm font-medium text-yellow-800 dark:text-yellow-200 mb-1">
                              Issues Found:
                            </h4>
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
                </ScrollArea>
              ) : (
                <div className="text-center py-12">
                  <PlayCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-lg font-medium mb-2">No dry run results</p>
                  <p className="text-muted-foreground">
                    Select files and start a dry run to see analysis results
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
