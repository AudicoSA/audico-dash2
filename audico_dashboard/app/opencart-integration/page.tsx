
'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useToast } from '@/hooks/use-toast'
import { 
  ShoppingCart, 
  Plus, 
  Edit, 
  Trash2, 
  CheckCircle, 
  XCircle, 
  Clock,
  Search,
  RefreshCw,
  ExternalLink,
  Wifi,
  WifiOff,
  AlertTriangle
} from 'lucide-react'
import { 
  fetchCategories, 
  createProduct, 
  updateProduct, 
  deleteProduct, 
  fetchProducts,
  testConnection,
  type OpenCartProduct,
  type OpenCartCategory,
  type ApiResponse
} from '@/lib/api'

interface TestResult {
  action: 'create' | 'update' | 'delete'
  product: OpenCartProduct & { id: string }
  status: 'success' | 'error' | 'pending'
  message: string
  timestamp: string
}

// Utility function to handle potentially double-wrapped API responses
function unwrapResponse<T>(response: any): ApiResponse<T> {
  // If response is already in the correct format
  if (response && typeof response === 'object' && 'success' in response) {
    return response as ApiResponse<T>
  }
  
  // If response is double-wrapped (response.data contains the actual response)
  if (response && response.data && typeof response.data === 'object' && 'success' in response.data) {
    return response.data as ApiResponse<T>
  }
  
  // If response is just the data without wrapper
  if (response && !('success' in response)) {
    return {
    success: true,
    data: response as T,
    message: 'Data retrieved successfully'
    }
  }
  
  // Fallback for unexpected response format
  return {
    success: false,
    error: 'Invalid response format',
    message: 'Received unexpected response format from API'
  }
}

// Safe array access utility
function ensureArray<T>(value: any): T[] {
  if (Array.isArray(value)) {
    return value
  }
  if (value === null || value === undefined) {
    return []
  }
  // If it's a single item, wrap it in an array
  return [value]
}

export default function OpenCartIntegration() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedProduct, setSelectedProduct] = useState<(OpenCartProduct & { id: string }) | null>(null)
  const [testResults, setTestResults] = useState<TestResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [categories, setCategories] = useState<OpenCartCategory[]>([])
  const [existingProducts, setExistingProducts] = useState<(OpenCartProduct & { id: string })[]>([])
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'testing'>('testing')
  const [initializationError, setInitializationError] = useState<string | null>(null)
  const { toast } = useToast()

  const [newProduct, setNewProduct] = useState({
    name: '',
    sku: '',
    price: '',
    description: '',
    category: '967', // Default to category_id 967 "Load"
    stock: ''
  })

  // Safe categories access with fallback
  const safeCategories = ensureArray<OpenCartCategory>(categories)

  // Load categories and test connection on component mount
  useEffect(() => {
    const initializeData = async () => {
    try {
    setInitializationError(null)
    
    // Test connection
    try {
    const connectionResult = await testConnection()
    const unwrappedConnection = unwrapResponse<{ status: string; version?: string }>(connectionResult)
    setConnectionStatus(unwrappedConnection.success ? 'connected' : 'disconnected')
    
    if (!unwrappedConnection.success) {
    console.warn('Connection test failed:', unwrappedConnection.error)
    }
    } catch (error) {
    console.error('Connection test error:', error)
    setConnectionStatus('disconnected')
    }
    
    // Load categories with error handling
    try {
    const categoriesResult = await fetchCategories()
    const unwrappedCategories = unwrapResponse<OpenCartCategory[]>(categoriesResult)
    
    if (unwrappedCategories.success && unwrappedCategories.data) {
    const categoriesArray = ensureArray<OpenCartCategory>(unwrappedCategories.data)
    setCategories(categoriesArray)
    } else {
    console.warn('Failed to load categories:', unwrappedCategories.error)
    setCategories([]) // Ensure categories is always an array
    toast({
    title: "Warning",
    description: "Failed to load categories. Using default options.",
    variant: "destructive"
    })
    }
    } catch (error) {
    console.error('Categories fetch error:', error)
    setCategories([]) // Ensure categories is always an array
    toast({
    title: "Error",
    description: "Failed to load categories from API",
    variant: "destructive"
    })
    }
    
    // Load existing products with error handling
    try {
    const productsResult = await fetchProducts()
    const unwrappedProducts = unwrapResponse<OpenCartProduct[]>(productsResult)
    
    if (unwrappedProducts.success && unwrappedProducts.data) {
    const productsArray = ensureArray<OpenCartProduct>(unwrappedProducts.data)
    const productsWithIds = productsArray.map(p => ({ 
    ...p, 
    id: p.id || Date.now().toString() + Math.random().toString(36).substr(2, 9)
    }))
    setExistingProducts(productsWithIds)
    } else {
    console.warn('Failed to load products:', unwrappedProducts.error)
    setExistingProducts([])
    }
    } catch (error) {
    console.error('Products fetch error:', error)
    setExistingProducts([])
    toast({
    title: "Warning",
    description: "Failed to load existing products",
    variant: "destructive"
    })
    }
    
    } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown initialization error'
    setInitializationError(errorMessage)
    console.error('Initialization error:', error)
    toast({
    title: "Initialization Error",
    description: errorMessage,
    variant: "destructive"
    })
    }
    }
    
    initializeData()
  }, [toast])

  const filteredProducts = existingProducts.filter(product =>
    product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (product.sku && product.sku.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  const handleCreateProduct = async () => {
    if (!newProduct.name || !newProduct.sku) {
    toast({
    title: "Validation Error",
    description: "Product name and SKU are required",
    variant: "destructive"
    })
    return
    }

    setIsLoading(true)
    
    try {
    const productData: OpenCartProduct = {
    name: newProduct.name,
    model: newProduct.sku, // Use SKU as model
    sku: newProduct.sku,
    price: parseFloat(newProduct.price) || 0,
    description: newProduct.description,
    category: newProduct.category,
    category_id: parseInt(newProduct.category) || 0,
    stock: parseInt(newProduct.stock) || 0,
    status: 'active'
    }
    
    const apiResult = await createProduct(productData)
    const unwrappedResult = unwrapResponse<OpenCartProduct>(apiResult)
    
    const result: TestResult = {
    action: 'create',
    product: {
    id: unwrappedResult.data?.id || Date.now().toString(),
    name: newProduct.name,
    model: newProduct.sku,
    sku: newProduct.sku,
    price: parseFloat(newProduct.price) || 0,
    description: newProduct.description,
    category: newProduct.category,
    status: 'active',
    stock: parseInt(newProduct.stock) || 0,
    lastUpdated: new Date().toISOString().split('T')[0]
    },
    status: unwrappedResult.success ? 'success' : 'error',
    message: unwrappedResult.message || (unwrappedResult.success ? 'Product created successfully' : 'Failed to create product'),
    timestamp: new Date().toISOString()
    }
    
    setTestResults(prev => [result, ...prev])
    
    if (unwrappedResult.success) {
    // Reset form but keep default category
    setNewProduct({
    name: '',
    sku: '',
    price: '',
    description: '',
    category: '967', // Keep default category
    stock: ''
    })
    
    // Refresh products list
    try {
    const productsResult = await fetchProducts()
    const unwrappedProducts = unwrapResponse<OpenCartProduct[]>(productsResult)
    if (unwrappedProducts.success && unwrappedProducts.data) {
    const productsArray = ensureArray<OpenCartProduct>(unwrappedProducts.data)
    const productsWithIds = productsArray.map(p => ({ 
    ...p, 
    id: p.id || Date.now().toString() + Math.random().toString(36).substr(2, 9)
    }))
    setExistingProducts(productsWithIds)
    }
    } catch (error) {
    console.error('Failed to refresh products list:', error)
    }
    
    toast({
    title: "Product created",
    description: `${newProduct.name} has been created successfully`,
    })
    } else {
    toast({
    title: "Error",
    description: unwrappedResult.error || 'Failed to create product',
    variant: "destructive"
    })
    }
    } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
    const result: TestResult = {
    action: 'create',
    product: {
    id: '',
    name: newProduct.name,
    model: newProduct.sku,
    sku: newProduct.sku,
    price: parseFloat(newProduct.price) || 0,
    description: newProduct.description,
    category: newProduct.category,
    status: 'active',
    stock: parseInt(newProduct.stock) || 0,
    lastUpdated: new Date().toISOString().split('T')[0]
    },
    status: 'error',
    message: errorMessage,
    timestamp: new Date().toISOString()
    }
    
    setTestResults(prev => [result, ...prev])
    
    toast({
    title: "Error",
    description: "Failed to create product",
    variant: "destructive"
    })
    } finally {
    setIsLoading(false)
    }
  }

  const handleUpdateProduct = async (product: OpenCartProduct & { id: string }) => {
    setIsLoading(true)
    
    try {
    const apiResult = await updateProduct(product.id, {
    name: product.name,
    sku: product.sku,
    price: product.price,
    description: product.description,
    category: product.category,
    stock: product.stock,
    status: product.status
    })
    
    const unwrappedResult = unwrapResponse<OpenCartProduct>(apiResult)
    
    const result: TestResult = {
    action: 'update',
    product,
    status: unwrappedResult.success ? 'success' : 'error',
    message: unwrappedResult.message || (unwrappedResult.success ? 'Product updated successfully' : 'Failed to update product'),
    timestamp: new Date().toISOString()
    }
    
    setTestResults(prev => [result, ...prev])
    
    if (unwrappedResult.success) {
    // Refresh products list
    try {
    const productsResult = await fetchProducts()
    const unwrappedProducts = unwrapResponse<OpenCartProduct[]>(productsResult)
    if (unwrappedProducts.success && unwrappedProducts.data) {
    const productsArray = ensureArray<OpenCartProduct>(unwrappedProducts.data)
    const productsWithIds = productsArray.map(p => ({ 
    ...p, 
    id: p.id || Date.now().toString() + Math.random().toString(36).substr(2, 9)
    }))
    setExistingProducts(productsWithIds)
    }
    } catch (error) {
    console.error('Failed to refresh products list:', error)
    }
    
    toast({
    title: "Product updated",
    description: `${product.name} has been updated successfully`,
    })
    } else {
    toast({
    title: "Error",
    description: unwrappedResult.error || 'Failed to update product',
    variant: "destructive"
    })
    }
    } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
    const result: TestResult = {
    action: 'update',
    product,
    status: 'error',
    message: errorMessage,
    timestamp: new Date().toISOString()
    }
    
    setTestResults(prev => [result, ...prev])
    
    toast({
    title: "Error",
    description: "Failed to update product",
    variant: "destructive"
    })
    } finally {
    setIsLoading(false)
    }
  }

  const handleDeleteProduct = async (product: OpenCartProduct & { id: string }) => {
    setIsLoading(true)
    
    try {
    const apiResult = await deleteProduct(product.id)
    const unwrappedResult = unwrapResponse<{ id: string }>(apiResult)
    
    const result: TestResult = {
    action: 'delete',
    product,
    status: unwrappedResult.success ? 'success' : 'error',
    message: unwrappedResult.message || (unwrappedResult.success ? 'Product deleted successfully' : 'Failed to delete product'),
    timestamp: new Date().toISOString()
    }
    
    setTestResults(prev => [result, ...prev])
    
    if (unwrappedResult.success) {
    // Refresh products list
    try {
    const productsResult = await fetchProducts()
    const unwrappedProducts = unwrapResponse<OpenCartProduct[]>(productsResult)
    if (unwrappedProducts.success && unwrappedProducts.data) {
    const productsArray = ensureArray<OpenCartProduct>(unwrappedProducts.data)
    const productsWithIds = productsArray.map(p => ({ 
    ...p, 
    id: p.id || Date.now().toString() + Math.random().toString(36).substr(2, 9)
    }))
    setExistingProducts(productsWithIds)
    }
    } catch (error) {
    console.error('Failed to refresh products list:', error)
    }
    
    toast({
    title: "Product deleted",
    description: `${product.name} has been deleted successfully`,
    })
    } else {
    toast({
    title: "Error",
    description: unwrappedResult.error || 'Failed to delete product',
    variant: "destructive"
    })
    }
    } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
    const result: TestResult = {
    action: 'delete',
    product,
    status: 'error',
    message: errorMessage,
    timestamp: new Date().toISOString()
    }
    
    setTestResults(prev => [result, ...prev])
    
    toast({
    title: "Error",
    description: "Failed to delete product",
    variant: "destructive"
    })
    } finally {
    setIsLoading(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
    case 'success':
    return <CheckCircle className="h-4 w-4 text-green-500" />
    case 'error':
    return <XCircle className="h-4 w-4 text-red-500" />
    default:
    return <Clock className="h-4 w-4 text-yellow-500" />
    }
  }

  const getActionBadge = (action: string) => {
    switch (action) {
    case 'create':
    return <Badge className="bg-green-100 text-green-800">Create</Badge>
    case 'update':
    return <Badge className="bg-blue-100 text-blue-800">Update</Badge>
    case 'delete':
    return <Badge className="bg-red-100 text-red-800">Delete</Badge>
    default:
    return <Badge>Unknown</Badge>
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
    <ShoppingCart className="h-8 w-8 text-green-500" />
    <h1 className="text-3xl font-bold">OpenCart Integration</h1>
    </div>
    <div className="flex items-center gap-2">
    {connectionStatus === 'connected' ? (
    <Badge className="bg-green-100 text-green-800 flex items-center gap-1">
    <Wifi className="h-3 w-3" />
    Connected
    </Badge>
    ) : connectionStatus === 'disconnected' ? (
    <Badge className="bg-red-100 text-red-800 flex items-center gap-1">
    <WifiOff className="h-3 w-3" />
    Disconnected
    </Badge>
    ) : (
    <Badge className="bg-yellow-100 text-yellow-800 flex items-center gap-1">
    <RefreshCw className="h-3 w-3 animate-spin" />
    Testing...
    </Badge>
    )}
    </div>
    </div>
    <p className="text-muted-foreground">
    Test product creation, updates, and synchronization with OpenCart store
    </p>
    
    {/* Initialization Error Display */}
    {initializationError && (
    <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
    <AlertTriangle className="h-4 w-4 text-red-500" />
    <span className="text-sm text-red-700">
    Initialization Error: {initializationError}
    </span>
    </div>
    )}
    </motion.div>

    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
    {/* Product Management */}
    <motion.div
    initial={{ opacity: 0, x: -20 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ delay: 0.1 }}
    className="space-y-6"
    >
    <Card className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-0 shadow-lg">
    <CardHeader>
    <CardTitle>Product Management</CardTitle>
    <CardDescription>
    Create new products or manage existing ones
    </CardDescription>
    </CardHeader>
    <CardContent>
    <Tabs defaultValue="create" className="w-full">
    <TabsList className="grid w-full grid-cols-2">
    <TabsTrigger value="create">Create Product</TabsTrigger>
    <TabsTrigger value="manage">Manage Existing</TabsTrigger>
    </TabsList>
    
    <TabsContent value="create" className="space-y-4">
    <div className="grid grid-cols-2 gap-4">
    <div className="space-y-2">
    <Label htmlFor="name">Product Name</Label>
    <Input
    id="name"
    value={newProduct.name}
    onChange={(e) => setNewProduct(prev => ({ ...prev, name: e.target.value }))}
    placeholder="Enter product name"
    />
    </div>
    <div className="space-y-2">
    <Label htmlFor="sku">SKU</Label>
    <Input
    id="sku"
    value={newProduct.sku}
    onChange={(e) => setNewProduct(prev => ({ ...prev, sku: e.target.value }))}
    placeholder="Enter SKU"
    />
    </div>
    </div>
    
    <div className="grid grid-cols-2 gap-4">
    <div className="space-y-2">
    <Label htmlFor="price">Price</Label>
    <Input
    id="price"
    type="number"
    value={newProduct.price}
    onChange={(e) => setNewProduct(prev => ({ ...prev, price: e.target.value }))}
    placeholder="0.00"
    />
    </div>
    <div className="space-y-2">
    <Label htmlFor="stock">Stock</Label>
    <Input
    id="stock"
    type="number"
    value={newProduct.stock}
    onChange={(e) => setNewProduct(prev => ({ ...prev, stock: e.target.value }))}
    placeholder="0"
    />
    </div>
    </div>
    
    <div className="space-y-2">
    <Label htmlFor="category">Category</Label>
    <Select value={newProduct.category} onValueChange={(value) => setNewProduct(prev => ({ ...prev, category: value }))}>
    <SelectTrigger>
    <SelectValue placeholder="Load (Default)" />
    </SelectTrigger>
    <SelectContent>
    <SelectItem value="967">Load (Default)</SelectItem>
    {safeCategories.length > 0 && (
    safeCategories.map((category) => (
    <SelectItem key={category.category_id} value={category.category_id.toString()}>
    {category.name}
    </SelectItem>
    ))
    )}
    </SelectContent>
    </Select>
    </div>
    
    <div className="space-y-2">
    <Label htmlFor="description">Description</Label>
    <Textarea
    id="description"
    value={newProduct.description}
    onChange={(e) => setNewProduct(prev => ({ ...prev, description: e.target.value }))}
    placeholder="Enter product description"
    rows={3}
    />
    </div>
    
    <Button 
    onClick={handleCreateProduct} 
    disabled={isLoading || !newProduct.name || !newProduct.sku}
    className="w-full"
    >
    {isLoading ? (
    <>
    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
    Creating...
    </>
    ) : (
    <>
    <Plus className="h-4 w-4 mr-2" />
    Create Product
    </>
    )}
    </Button>
    </TabsContent>
    
    <TabsContent value="manage" className="space-y-4">
    <div className="space-y-2">
    <Label htmlFor="search">Search Products</Label>
    <div className="relative">
    <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
    <Input
    id="search"
    value={searchTerm}
    onChange={(e) => setSearchTerm(e.target.value)}
    placeholder="Search by name or SKU"
    className="pl-10"
    />
    </div>
    </div>
    
    <div className="space-y-2 max-h-64 overflow-y-auto">
    {filteredProducts.length > 0 ? (
    filteredProducts.map((product) => (
    <div key={product.id} className="border rounded-lg p-3">
    <div className="flex items-center justify-between">
    <div>
    <p className="font-medium">{product.name}</p>
    <p className="text-sm text-muted-foreground">
    {product.sku} • ${product.price} • Stock: {product.stock || product.quantity || 0}
    </p>
    </div>
    <div className="flex gap-2">
    <Button
    variant="outline"
    size="sm"
    onClick={() => handleUpdateProduct(product)}
    disabled={isLoading}
    >
    <Edit className="h-4 w-4" />
    </Button>
    <Button
    variant="outline"
    size="sm"
    onClick={() => handleDeleteProduct(product)}
    disabled={isLoading}
    >
    <Trash2 className="h-4 w-4" />
    </Button>
    </div>
    </div>
    </div>
    ))
    ) : (
    <div className="text-center py-4 text-muted-foreground">
    No products found
    </div>
    )}
    </div>
    </TabsContent>
    </Tabs>
    </CardContent>
    </Card>
    </motion.div>

    {/* Test Results */}
    <motion.div
    initial={{ opacity: 0, x: 20 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ delay: 0.2 }}
    >
    <Card className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-0 shadow-lg">
    <CardHeader>
    <CardTitle className="flex items-center justify-between">
    Test Results
    <Button variant="outline" size="sm">
    <ExternalLink className="h-4 w-4 mr-1" />
    View Store
    </Button>
    </CardTitle>
    <CardDescription>
    Recent API operations and their results
    </CardDescription>
    </CardHeader>
    <CardContent>
    {testResults.length > 0 ? (
    <div className="space-y-4 max-h-96 overflow-y-auto">
    {testResults.map((result, index) => (
    <div key={index} className="border rounded-lg p-4">
    <div className="flex items-center justify-between mb-2">
    <div className="flex items-center gap-2">
    {getStatusIcon(result.status)}
    {getActionBadge(result.action)}
    <span className="font-medium">{result.product.name}</span>
    </div>
    <span className="text-xs text-muted-foreground">
    {new Date(result.timestamp).toLocaleTimeString()}
    </span>
    </div>
    
    <p className="text-sm text-muted-foreground mb-2">
    {result.message}
    </p>
    
    <div className="text-xs text-muted-foreground">
    SKU: {result.product.sku} • Price: ${result.product.price}
    </div>
    </div>
    ))}
    </div>
    ) : (
    <div className="text-center py-8">
    <ShoppingCart className="h-12 w-12 text-gray-400 mx-auto mb-4" />
    <p className="text-lg font-medium mb-2">No operations yet</p>
    <p className="text-muted-foreground">
    Create, update, or delete products to see test results
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
