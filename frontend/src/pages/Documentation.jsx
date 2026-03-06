import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  ArrowLeft,
  BookOpen,
  Code,
  Globe,
  FileText,
  Users,
  Bed,
  Receipt,
  MessageCircle,
  Shield,
  Bell,
  Calendar,
  Settings,
  Download,
  ExternalLink,
  Copy,
  CheckCheck,
  RefreshCw,
  Mail,
  Smartphone,
  Database,
  Cloud,
  Train,
  Home,
  ClipboardList,
  FileBarChart,
  UserCheck,
  DoorOpen,
  Clock,
  Key
} from "lucide-react";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Documentation() {
  const navigate = useNavigate();
  const [copiedCode, setCopiedCode] = useState(null);

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedCode(id);
    toast.success("Copied to clipboard!");
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const CodeBlock = ({ code, id, language = "bash" }) => (
    <div className="relative group">
      <pre className="bg-black/80 border border-vault-border rounded-lg p-4 overflow-x-auto text-sm font-mono text-vault-text">
        <code>{code}</code>
      </pre>
      <Button
        variant="ghost"
        size="sm"
        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={() => copyToClipboard(code, id)}
      >
        {copiedCode === id ? <CheckCheck className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
      </Button>
    </div>
  );

  const FeatureCard = ({ icon: Icon, title, description, status = "active" }) => (
    <div className="bg-vault-surface-highlight border border-vault-border rounded-lg p-4">
      <div className="flex items-start gap-3">
        <div className={`p-2 rounded-lg ${status === "active" ? "bg-vault-gold/20" : "bg-vault-border"}`}>
          <Icon className={`w-5 h-5 ${status === "active" ? "text-vault-gold" : "text-vault-text-secondary"}`} />
        </div>
        <div className="flex-1">
          <h4 className="font-semibold text-vault-text mb-1">{title}</h4>
          <p className="text-sm text-vault-text-secondary">{description}</p>
          {status !== "active" && (
            <span className="inline-block mt-2 text-xs px-2 py-0.5 bg-amber-500/20 text-amber-400 rounded">
              {status}
            </span>
          )}
        </div>
      </div>
    </div>
  );

  const EndpointRow = ({ method, path, description }) => (
    <tr className="border-b border-vault-border hover:bg-vault-surface-highlight/50">
      <td className="py-3 px-4">
        <span className={`px-2 py-1 rounded text-xs font-mono font-bold ${
          method === "GET" ? "bg-green-500/20 text-green-400" :
          method === "POST" ? "bg-blue-500/20 text-blue-400" :
          method === "PUT" ? "bg-amber-500/20 text-amber-400" :
          "bg-red-500/20 text-red-400"
        }`}>
          {method}
        </span>
      </td>
      <td className="py-3 px-4 font-mono text-sm text-vault-gold">{path}</td>
      <td className="py-3 px-4 text-sm text-vault-text-secondary">{description}</td>
    </tr>
  );

  return (
    <div className="min-h-screen bg-vault-bg grid-bg" data-testid="documentation-page">
      {/* Header */}
      <div className="bg-vault-surface border-b border-vault-border sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button 
              variant="ghost" 
              onClick={() => navigate("/admin/dashboard")}
              className="text-vault-text-secondary hover:text-vault-gold"
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div className="flex items-center gap-3">
              <img 
                src="https://customer-assets.emergentagent.com/job_guest-hotel-mgmt/artifacts/56yphta2_17721406444867042425090808501904.jpg" 
                alt="Hodler Inn Logo" 
                className="w-10 h-10 rounded-lg object-cover"
              />
              <div>
                <h1 className="font-outfit font-bold text-vault-text text-xl">Documentation</h1>
                <p className="text-xs text-vault-text-secondary">Hodler Inn System Guide</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              size="sm"
              className="border-vault-border text-vault-text-secondary"
              onClick={() => window.open("/demo", "_blank")}
            >
              <Globe className="w-4 h-4 mr-2" />
              Demo Portal
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              className="border-vault-border text-vault-text-secondary"
              onClick={() => window.open("/demo/admin", "_blank")}
            >
              <Shield className="w-4 h-4 mr-2" />
              Demo Admin
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList className="bg-vault-surface border border-vault-border p-1 flex flex-wrap gap-1">
              <TabsTrigger value="overview" className="data-[state=active]:bg-vault-gold data-[state=active]:text-black">
                <BookOpen className="w-4 h-4 mr-2" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="features" className="data-[state=active]:bg-vault-gold data-[state=active]:text-black">
                <FileText className="w-4 h-4 mr-2" />
                Features
              </TabsTrigger>
              <TabsTrigger value="demo" className="data-[state=active]:bg-vault-gold data-[state=active]:text-black">
                <Globe className="w-4 h-4 mr-2" />
                Demo Mode
              </TabsTrigger>
              <TabsTrigger value="api" className="data-[state=active]:bg-vault-gold data-[state=active]:text-black">
                <Code className="w-4 h-4 mr-2" />
                Billing API
              </TabsTrigger>
              <TabsTrigger value="chatbot" className="data-[state=active]:bg-vault-gold data-[state=active]:text-black">
                <MessageCircle className="w-4 h-4 mr-2" />
                Bitsy Chatbot
              </TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-6">
              <Card className="bg-vault-surface border-vault-border">
                <CardHeader>
                  <CardTitle className="font-outfit text-2xl text-vault-text flex items-center gap-3">
                    <Home className="w-7 h-7 text-vault-gold" />
                    Hodler Inn Management System
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <p className="text-vault-text-secondary leading-relaxed">
                    A comprehensive railroad crew accommodation management platform designed for Hodler Inn. 
                    This system handles guest check-ins, room management, billing, automated sync with railroad portals, 
                    and includes an AI-powered booking chatbot.
                  </p>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-gradient-to-br from-vault-gold/10 to-vault-gold/5 border border-vault-gold/20 rounded-lg p-4">
                      <Train className="w-8 h-8 text-vault-gold mb-3" />
                      <h3 className="font-bold text-vault-text mb-1">Railroad Integration</h3>
                      <p className="text-sm text-vault-text-secondary">
                        Automated sync with API Global railroad portal for billing verification
                      </p>
                    </div>
                    <div className="bg-gradient-to-br from-blue-500/10 to-blue-500/5 border border-blue-500/20 rounded-lg p-4">
                      <MessageCircle className="w-8 h-8 text-blue-400 mb-3" />
                      <h3 className="font-bold text-vault-text mb-1">AI Chatbot (Bitsy)</h3>
                      <p className="text-sm text-vault-text-secondary">
                        Conversational booking agent with voice input and real-time availability
                      </p>
                    </div>
                    <div className="bg-gradient-to-br from-green-500/10 to-green-500/5 border border-green-500/20 rounded-lg p-4">
                      <Bell className="w-8 h-8 text-green-400 mb-3" />
                      <h3 className="font-bold text-vault-text mb-1">Smart Notifications</h3>
                      <p className="text-sm text-vault-text-secondary">
                        Email & Telegram alerts for occupancy, check-ins, and room status
                      </p>
                    </div>
                  </div>

                  <div className="border-t border-vault-border pt-6">
                    <h3 className="font-outfit text-lg text-vault-text mb-4">Quick Links</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <a href="/" target="_blank" className="flex items-center gap-2 p-3 bg-vault-surface-highlight border border-vault-border rounded-lg hover:border-vault-gold transition-colors">
                        <Users className="w-5 h-5 text-vault-gold" />
                        <span className="text-sm text-vault-text">Guest Portal</span>
                      </a>
                      <a href="/admin" target="_blank" className="flex items-center gap-2 p-3 bg-vault-surface-highlight border border-vault-border rounded-lg hover:border-vault-gold transition-colors">
                        <Shield className="w-5 h-5 text-vault-gold" />
                        <span className="text-sm text-vault-text">Admin Login</span>
                      </a>
                      <a href="/book" target="_blank" className="flex items-center gap-2 p-3 bg-vault-surface-highlight border border-vault-border rounded-lg hover:border-vault-gold transition-colors">
                        <MessageCircle className="w-5 h-5 text-vault-gold" />
                        <span className="text-sm text-vault-text">Book Now</span>
                      </a>
                      <a href="/demo" target="_blank" className="flex items-center gap-2 p-3 bg-vault-surface-highlight border border-vault-border rounded-lg hover:border-vault-gold transition-colors">
                        <Globe className="w-5 h-5 text-vault-gold" />
                        <span className="text-sm text-vault-text">Demo Mode</span>
                      </a>
                    </div>
                  </div>

                  <div className="border-t border-vault-border pt-6">
                    <h3 className="font-outfit text-lg text-vault-text mb-4">Business Information</h3>
                    <div className="bg-vault-surface-highlight border border-vault-border rounded-lg p-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <p className="text-vault-text-secondary text-sm">Address</p>
                          <p className="text-vault-text font-medium">820 US-59, Heavener, OK 74937</p>
                        </div>
                        <div>
                          <p className="text-vault-text-secondary text-sm">Property Type</p>
                          <p className="text-vault-text font-medium">Railroad Crew Accommodation</p>
                        </div>
                        <div>
                          <p className="text-vault-text-secondary text-sm">Total Rooms</p>
                          <p className="text-vault-text font-medium">28 Rooms</p>
                        </div>
                        <div>
                          <p className="text-vault-text-secondary text-sm">Railroad Partner</p>
                          <p className="text-vault-text font-medium">CPKC (Canadian Pacific Kansas City)</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Features Tab */}
            <TabsContent value="features" className="space-y-6">
              <Card className="bg-vault-surface border-vault-border">
                <CardHeader>
                  <CardTitle className="font-outfit text-xl text-vault-text">System Features</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <FeatureCard
                      icon={Users}
                      title="Guest Portal"
                      description="Self-service kiosk for railroad crew to check in/out with employee ID verification and digital signatures"
                    />
                    <FeatureCard
                      icon={Shield}
                      title="Admin Dashboard"
                      description="Comprehensive admin panel with guest records, room management, billing reports, and sync controls"
                    />
                    <FeatureCard
                      icon={Bed}
                      title="Room Management"
                      description="Track room status (clean/dirty), occupancy, maintenance, and manage both railroad and other guests"
                    />
                    <FeatureCard
                      icon={Receipt}
                      title="Billing Reports"
                      description="Automated billing calculation based on 24-hour periods with Excel, PDF, and PNG exports"
                    />
                    <FeatureCard
                      icon={RefreshCw}
                      title="Auto-Sync (AI Agent)"
                      description="Daily automated sync with API Global railroad portal at 3 PM to verify billing records"
                    />
                    <FeatureCard
                      icon={UserCheck}
                      title="Employee Verification"
                      description="Maintain approved employee list with bulk import and portal collection features"
                    />
                    <FeatureCard
                      icon={Bell}
                      title="Email Alerts"
                      description="Automated notifications for sold-out, rooms available, low availability (heads-up), and daily status"
                    />
                    <FeatureCard
                      icon={Mail}
                      title="Per-Recipient Alerts"
                      description="Customize which email alerts each recipient receives (sold-out, available, heads-up, daily)"
                    />
                    <FeatureCard
                      icon={MessageCircle}
                      title="AI Chatbot (Bitsy)"
                      description="Conversational booking agent with voice input, dynamic pricing, and real-time availability"
                    />
                    <FeatureCard
                      icon={Globe}
                      title="Demo Mode"
                      description="Sandboxed demo environment with separate database for safe testing and demonstrations"
                    />
                    <FeatureCard
                      icon={Cloud}
                      title="Zoho Integration"
                      description="Automated daily backups to Zoho WorkDrive cloud storage"
                    />
                    <FeatureCard
                      icon={Smartphone}
                      title="Telegram Notifications"
                      description="Real-time notifications via Telegram with interactive buttons for room cleaning"
                    />
                    <FeatureCard
                      icon={Calendar}
                      title="Manual Entry"
                      description="Back-dated entry form for adding historical check-ins to billing records"
                    />
                    <FeatureCard
                      icon={FileBarChart}
                      title="Guarantee Report"
                      description="Track revenue losses from turned-away guests when holding rooms for railroad"
                    />
                    <FeatureCard
                      icon={Train}
                      title="CPKC Email Scraper"
                      description="Automatically parse PDF booking sheets from CPKC emails for expected arrivals"
                      status="New"
                    />
                    <FeatureCard
                      icon={DoorOpen}
                      title="Auto-Dirty Rooms"
                      description="Automatically mark rooms as dirty 20 minutes after checkout with Telegram notifications"
                    />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-vault-surface border-vault-border">
                <CardHeader>
                  <CardTitle className="font-outfit text-xl text-vault-text">Admin Panel Sections</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center gap-3 p-3 bg-vault-surface-highlight border border-vault-border rounded-lg">
                      <ClipboardList className="w-5 h-5 text-vault-gold" />
                      <div>
                        <h4 className="font-medium text-vault-text">Sign-In Sheet</h4>
                        <p className="text-sm text-vault-text-secondary">View and export guest sign-in records with signatures</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 p-3 bg-vault-surface-highlight border border-vault-border rounded-lg">
                      <Receipt className="w-5 h-5 text-vault-gold" />
                      <div>
                        <h4 className="font-medium text-vault-text">Billing Report</h4>
                        <p className="text-sm text-vault-text-secondary">View billing calculations and export to Excel/PDF/PNG</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 p-3 bg-vault-surface-highlight border border-vault-border rounded-lg">
                      <Bed className="w-5 h-5 text-vault-gold" />
                      <div>
                        <h4 className="font-medium text-vault-text">Room Management</h4>
                        <p className="text-sm text-vault-text-secondary">Manage rooms, other guests, reservations, and cleaning status</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 p-3 bg-vault-surface-highlight border border-vault-border rounded-lg">
                      <Users className="w-5 h-5 text-vault-gold" />
                      <div>
                        <h4 className="font-medium text-vault-text">Employee List</h4>
                        <p className="text-sm text-vault-text-secondary">Manage approved employee IDs with bulk import and portal sync</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 p-3 bg-vault-surface-highlight border border-vault-border rounded-lg">
                      <UserCheck className="w-5 h-5 text-vault-gold" />
                      <div>
                        <h4 className="font-medium text-vault-text">Guest Verification</h4>
                        <p className="text-sm text-vault-text-secondary">Verify, flag, or block guests; bulk verification support</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 p-3 bg-vault-surface-highlight border border-vault-border rounded-lg">
                      <FileBarChart className="w-5 h-5 text-vault-gold" />
                      <div>
                        <h4 className="font-medium text-vault-text">Guarantee Report</h4>
                        <p className="text-sm text-vault-text-secondary">Track room guarantees and turned-away guest revenue loss</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 p-3 bg-vault-surface-highlight border border-vault-border rounded-lg">
                      <Settings className="w-5 h-5 text-vault-gold" />
                      <div>
                        <h4 className="font-medium text-vault-text">Portal Settings</h4>
                        <p className="text-sm text-vault-text-secondary">Configure sync, email, Telegram, voice, chatbot, and integrations</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Demo Mode Tab */}
            <TabsContent value="demo" className="space-y-6">
              <Card className="bg-vault-surface border-vault-border">
                <CardHeader>
                  <CardTitle className="font-outfit text-xl text-vault-text flex items-center gap-2">
                    <Globe className="w-6 h-6 text-vault-gold" />
                    Demo Mode
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-lg p-4">
                    <p className="text-vault-text leading-relaxed">
                      Demo Mode provides a fully functional, sandboxed version of the application. 
                      It uses a <strong>separate database</strong> so you can test all features without affecting production data.
                      Perfect for training, demonstrations, and testing new workflows.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="font-semibold text-vault-text mb-3 flex items-center gap-2">
                        <Users className="w-5 h-5 text-vault-gold" />
                        Demo Guest Portal
                      </h3>
                      <div className="bg-vault-surface-highlight border border-vault-border rounded-lg p-4">
                        <p className="text-sm text-vault-text-secondary mb-4">
                          Test the guest check-in/check-out experience with sample employee IDs.
                        </p>
                        <div className="space-y-2 mb-4">
                          <p className="text-xs text-vault-text-secondary">Sample Employee IDs:</p>
                          <div className="flex flex-wrap gap-2">
                            <code className="px-2 py-1 bg-black/50 rounded text-vault-gold text-sm">EMP001</code>
                            <code className="px-2 py-1 bg-black/50 rounded text-vault-gold text-sm">EMP002</code>
                            <code className="px-2 py-1 bg-black/50 rounded text-vault-gold text-sm">EMP003</code>
                          </div>
                        </div>
                        <Button 
                          variant="outline" 
                          className="w-full border-vault-gold text-vault-gold hover:bg-vault-gold hover:text-black"
                          onClick={() => window.open("/demo", "_blank")}
                        >
                          <ExternalLink className="w-4 h-4 mr-2" />
                          Open Demo Portal
                        </Button>
                      </div>
                    </div>

                    <div>
                      <h3 className="font-semibold text-vault-text mb-3 flex items-center gap-2">
                        <Shield className="w-5 h-5 text-vault-gold" />
                        Demo Admin Panel
                      </h3>
                      <div className="bg-vault-surface-highlight border border-vault-border rounded-lg p-4">
                        <p className="text-sm text-vault-text-secondary mb-4">
                          Full admin functionality with demo data. Reset data anytime.
                        </p>
                        <div className="space-y-2 mb-4">
                          <p className="text-xs text-vault-text-secondary">Admin Password:</p>
                          <code className="block px-2 py-1 bg-black/50 rounded text-vault-gold text-sm">hodlerinn2024</code>
                        </div>
                        <Button 
                          variant="outline" 
                          className="w-full border-vault-gold text-vault-gold hover:bg-vault-gold hover:text-black"
                          onClick={() => window.open("/demo/admin", "_blank")}
                        >
                          <ExternalLink className="w-4 h-4 mr-2" />
                          Open Demo Admin
                        </Button>
                      </div>
                    </div>
                  </div>

                  <div className="border-t border-vault-border pt-6">
                    <h3 className="font-semibold text-vault-text mb-3">Demo Features</h3>
                    <ul className="space-y-2 text-sm text-vault-text-secondary">
                      <li className="flex items-center gap-2">
                        <CheckCheck className="w-4 h-4 text-green-400" />
                        Separate demo database - no impact on production
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCheck className="w-4 h-4 text-green-400" />
                        Pre-loaded sample rooms, employees, and bookings
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCheck className="w-4 h-4 text-green-400" />
                        Reset button to restore demo data anytime
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCheck className="w-4 h-4 text-green-400" />
                        All admin features functional in demo mode
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCheck className="w-4 h-4 text-green-400" />
                        Perfect for training staff and client demos
                      </li>
                    </ul>
                  </div>

                  <div className="border-t border-vault-border pt-6">
                    <h3 className="font-semibold text-vault-text mb-3">Demo API Endpoints</h3>
                    <CodeBlock
                      id="demo-api"
                      code={`# Initialize/Reset Demo Data
POST ${API.replace('/api', '')}/api/demo/init

# Get Demo Rooms
GET ${API.replace('/api', '')}/api/demo/rooms

# Get Demo Guests
GET ${API.replace('/api', '')}/api/demo/guests

# Get Demo Employees
GET ${API.replace('/api', '')}/api/demo/employees`}
                    />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Billing API Tab */}
            <TabsContent value="api" className="space-y-6">
              <Card className="bg-vault-surface border-vault-border">
                <CardHeader>
                  <CardTitle className="font-outfit text-xl text-vault-text flex items-center gap-2">
                    <Code className="w-6 h-6 text-vault-gold" />
                    Billing & Admin API Reference
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4">
                    <p className="text-vault-text text-sm">
                      <strong>Base URL:</strong> <code className="text-vault-gold">{API.replace('/api', '')}/api</code>
                    </p>
                    <p className="text-vault-text-secondary text-sm mt-2">
                      Admin endpoints require authentication via the admin login.
                    </p>
                  </div>

                  {/* Billing Endpoints */}
                  <div>
                    <h3 className="font-semibold text-vault-text mb-3 flex items-center gap-2">
                      <Receipt className="w-5 h-5 text-vault-gold" />
                      Billing Endpoints
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="w-full border border-vault-border rounded-lg">
                        <thead className="bg-vault-surface-highlight">
                          <tr className="border-b border-vault-border">
                            <th className="py-2 px-4 text-left text-vault-gold text-sm">Method</th>
                            <th className="py-2 px-4 text-left text-vault-gold text-sm">Endpoint</th>
                            <th className="py-2 px-4 text-left text-vault-gold text-sm">Description</th>
                          </tr>
                        </thead>
                        <tbody>
                          <EndpointRow method="GET" path="/admin/records" description="Get all guest records with billing info" />
                          <EndpointRow method="GET" path="/admin/export-billing" description="Export billing report as Excel" />
                          <EndpointRow method="GET" path="/admin/export-billing-pdf" description="Export billing report as PDF" />
                          <EndpointRow method="GET" path="/admin/export-billing-png" description="Export billing report as PNG image" />
                          <EndpointRow method="GET" path="/admin/guarantee-report" description="Get guarantee report with revenue loss" />
                          <EndpointRow method="GET" path="/admin/export-guarantee-report" description="Export guarantee report as Excel" />
                          <EndpointRow method="POST" path="/admin/turned-away" description="Log a turned-away guest" />
                          <EndpointRow method="GET" path="/admin/turned-away" description="Get turned-away guests list" />
                          <EndpointRow method="DELETE" path="/admin/turned-away/{id}" description="Delete turned-away record" />
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Guest Endpoints */}
                  <div>
                    <h3 className="font-semibold text-vault-text mb-3 flex items-center gap-2">
                      <Users className="w-5 h-5 text-vault-gold" />
                      Guest Management Endpoints
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="w-full border border-vault-border rounded-lg">
                        <thead className="bg-vault-surface-highlight">
                          <tr className="border-b border-vault-border">
                            <th className="py-2 px-4 text-left text-vault-gold text-sm">Method</th>
                            <th className="py-2 px-4 text-left text-vault-gold text-sm">Endpoint</th>
                            <th className="py-2 px-4 text-left text-vault-gold text-sm">Description</th>
                          </tr>
                        </thead>
                        <tbody>
                          <EndpointRow method="POST" path="/checkin" description="Check in a guest" />
                          <EndpointRow method="POST" path="/checkout" description="Check out a guest" />
                          <EndpointRow method="GET" path="/guests/{employee_number}" description="Get guest by employee number" />
                          <EndpointRow method="POST" path="/guests/register" description="Register new guest" />
                          <EndpointRow method="GET" path="/admin/guests" description="Get all registered guests" />
                          <EndpointRow method="POST" path="/admin/guests/{id}/verify" description="Verify a guest" />
                          <EndpointRow method="POST" path="/admin/guests/bulk-verify" description="Bulk verify guests" />
                          <EndpointRow method="POST" path="/admin/manual-entry" description="Add back-dated entry" />
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Room Endpoints */}
                  <div>
                    <h3 className="font-semibold text-vault-text mb-3 flex items-center gap-2">
                      <Bed className="w-5 h-5 text-vault-gold" />
                      Room Management Endpoints
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="w-full border border-vault-border rounded-lg">
                        <thead className="bg-vault-surface-highlight">
                          <tr className="border-b border-vault-border">
                            <th className="py-2 px-4 text-left text-vault-gold text-sm">Method</th>
                            <th className="py-2 px-4 text-left text-vault-gold text-sm">Endpoint</th>
                            <th className="py-2 px-4 text-left text-vault-gold text-sm">Description</th>
                          </tr>
                        </thead>
                        <tbody>
                          <EndpointRow method="GET" path="/admin/rooms" description="Get all rooms" />
                          <EndpointRow method="POST" path="/admin/rooms" description="Create a room" />
                          <EndpointRow method="PUT" path="/admin/rooms/{id}" description="Update a room" />
                          <EndpointRow method="DELETE" path="/admin/rooms/{id}" description="Delete a room" />
                          <EndpointRow method="POST" path="/admin/rooms/{number}/mark-dirty" description="Mark room as dirty" />
                          <EndpointRow method="POST" path="/admin/rooms/{number}/mark-clean" description="Mark room as clean" />
                          <EndpointRow method="POST" path="/admin/rooms/block" description="Block room for other guest" />
                          <EndpointRow method="POST" path="/admin/rooms/unblock/{number}" description="Unblock/checkout other guest" />
                          <EndpointRow method="GET" path="/admin/rooms/blocked" description="Get blocked rooms" />
                          <EndpointRow method="GET" path="/admin/rooms/reservations" description="Get reservations" />
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Sync Endpoints */}
                  <div>
                    <h3 className="font-semibold text-vault-text mb-3 flex items-center gap-2">
                      <RefreshCw className="w-5 h-5 text-vault-gold" />
                      Sync & Portal Endpoints
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="w-full border border-vault-border rounded-lg">
                        <thead className="bg-vault-surface-highlight">
                          <tr className="border-b border-vault-border">
                            <th className="py-2 px-4 text-left text-vault-gold text-sm">Method</th>
                            <th className="py-2 px-4 text-left text-vault-gold text-sm">Endpoint</th>
                            <th className="py-2 px-4 text-left text-vault-gold text-sm">Description</th>
                          </tr>
                        </thead>
                        <tbody>
                          <EndpointRow method="GET" path="/admin/sync/status" description="Get sync status" />
                          <EndpointRow method="POST" path="/admin/sync/run" description="Run sync manually" />
                          <EndpointRow method="POST" path="/admin/sync/reset" description="Reset sync status" />
                          <EndpointRow method="GET" path="/admin/sync/history" description="Get sync history" />
                          <EndpointRow method="GET" path="/admin/settings" description="Get portal settings" />
                          <EndpointRow method="POST" path="/admin/settings" description="Update portal settings" />
                          <EndpointRow method="POST" path="/admin/settings/test-connection" description="Test portal connection" />
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Example Code */}
                  <div className="border-t border-vault-border pt-6">
                    <h3 className="font-semibold text-vault-text mb-3">Example: Get Billing Records</h3>
                    <CodeBlock
                      id="billing-example"
                      code={`# Get billing records with date filter
curl -X GET "${API}/admin/records?start_date=2025-03-01&end_date=2025-03-31"

# Export billing report as Excel
curl -X GET "${API}/admin/export-billing?start_date=2025-03-01&end_date=2025-03-31" \\
  -o billing_report.xlsx

# Export billing report as PDF
curl -X GET "${API}/admin/export-billing-pdf" -o billing_report.pdf`}
                    />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Chatbot Tab */}
            <TabsContent value="chatbot" className="space-y-6">
              <Card className="bg-vault-surface border-vault-border">
                <CardHeader>
                  <CardTitle className="font-outfit text-xl text-vault-text flex items-center gap-2">
                    <MessageCircle className="w-6 h-6 text-vault-gold" />
                    Bitsy AI Chatbot
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-lg p-4">
                    <p className="text-vault-text leading-relaxed">
                      <strong>Bitsy</strong> is an AI-powered booking assistant that handles the entire reservation flow.
                      It collects guest information, checks real-time availability, calculates pricing with tax,
                      and creates reservations. Bitsy also supports voice input for hands-free operation.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="font-semibold text-vault-text mb-3">Features</h3>
                      <ul className="space-y-2 text-sm text-vault-text-secondary">
                        <li className="flex items-center gap-2">
                          <CheckCheck className="w-4 h-4 text-green-400" />
                          Conversational booking flow
                        </li>
                        <li className="flex items-center gap-2">
                          <CheckCheck className="w-4 h-4 text-green-400" />
                          Voice input support (microphone)
                        </li>
                        <li className="flex items-center gap-2">
                          <CheckCheck className="w-4 h-4 text-green-400" />
                          Real-time availability checking
                        </li>
                        <li className="flex items-center gap-2">
                          <CheckCheck className="w-4 h-4 text-green-400" />
                          Dynamic pricing (single/double bed)
                        </li>
                        <li className="flex items-center gap-2">
                          <CheckCheck className="w-4 h-4 text-green-400" />
                          Sales tax calculation
                        </li>
                        <li className="flex items-center gap-2">
                          <CheckCheck className="w-4 h-4 text-green-400" />
                          Email confirmations
                        </li>
                        <li className="flex items-center gap-2">
                          <CheckCheck className="w-4 h-4 text-green-400" />
                          Telegram notifications to admin
                        </li>
                        <li className="flex items-center gap-2">
                          <CheckCheck className="w-4 h-4 text-green-400" />
                          CPKC priority room blocking
                        </li>
                      </ul>
                    </div>

                    <div>
                      <h3 className="font-semibold text-vault-text mb-3">Admin Settings</h3>
                      <div className="space-y-3">
                        <div className="bg-vault-surface-highlight border border-vault-border rounded-lg p-3">
                          <p className="text-xs text-vault-text-secondary">Single Bed Rate</p>
                          <p className="text-vault-gold font-mono">Configurable in Settings</p>
                        </div>
                        <div className="bg-vault-surface-highlight border border-vault-border rounded-lg p-3">
                          <p className="text-xs text-vault-text-secondary">Double Bed Rate</p>
                          <p className="text-vault-gold font-mono">Configurable in Settings</p>
                        </div>
                        <div className="bg-vault-surface-highlight border border-vault-border rounded-lg p-3">
                          <p className="text-xs text-vault-text-secondary">Sales Tax Rate</p>
                          <p className="text-vault-gold font-mono">Configurable in Settings</p>
                        </div>
                        <div className="bg-vault-surface-highlight border border-vault-border rounded-lg p-3">
                          <p className="text-xs text-vault-text-secondary">Max Rooms per Day</p>
                          <p className="text-vault-gold font-mono">Configurable in Settings</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="border-t border-vault-border pt-6">
                    <h3 className="font-semibold text-vault-text mb-3">Chatbot API Endpoints</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full border border-vault-border rounded-lg">
                        <thead className="bg-vault-surface-highlight">
                          <tr className="border-b border-vault-border">
                            <th className="py-2 px-4 text-left text-vault-gold text-sm">Method</th>
                            <th className="py-2 px-4 text-left text-vault-gold text-sm">Endpoint</th>
                            <th className="py-2 px-4 text-left text-vault-gold text-sm">Description</th>
                          </tr>
                        </thead>
                        <tbody>
                          <EndpointRow method="POST" path="/chatbot/message" description="Send message to chatbot" />
                          <EndpointRow method="GET" path="/chatbot/availability" description="Check room availability" />
                          <EndpointRow method="POST" path="/chatbot/transcribe" description="Transcribe voice to text" />
                          <EndpointRow method="GET" path="/chatbot/history/{session_id}" description="Get chat history" />
                          <EndpointRow method="DELETE" path="/chatbot/session/{session_id}" description="Delete chat session" />
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div className="border-t border-vault-border pt-6">
                    <h3 className="font-semibold text-vault-text mb-3">WordPress Embed Code</h3>
                    <p className="text-sm text-vault-text-secondary mb-4">
                      Add the chatbot to your WordPress site as a floating widget that appears on all pages.
                    </p>
                    <CodeBlock
                      id="embed-code"
                      code={`<!-- Bitsy Chatbot Widget -->
<div id="bitsy-chat-widget"></div>
<style>
#bitsy-chat-widget {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 99999;
}
#bitsy-chat-button {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(30, 58, 95, 0.4);
}
#bitsy-chat-iframe-container {
  display: none;
  position: fixed;
  bottom: 90px;
  right: 20px;
  width: 380px;
  height: 600px;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}
#bitsy-chat-iframe-container.open { display: block; }
</style>
<script>
(function() {
  var widget = document.getElementById('bitsy-chat-widget');
  var button = document.createElement('button');
  button.id = 'bitsy-chat-button';
  button.innerHTML = '<svg viewBox="0 0 24 24" fill="white" width="28" height="28"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>';
  widget.appendChild(button);
  
  var container = document.createElement('div');
  container.id = 'bitsy-chat-iframe-container';
  container.innerHTML = '<iframe id="bitsy-chat-iframe" src="https://cpkc.hodlerinn.com/book" style="width:100%;height:100%;border:none;" allow="microphone"></iframe>';
  widget.appendChild(container);
  
  button.onclick = function() { container.classList.toggle('open'); };
})();
</script>`}
                    />
                    <div className="mt-4">
                      <Button 
                        variant="outline" 
                        className="border-vault-gold text-vault-gold hover:bg-vault-gold hover:text-black"
                        onClick={() => window.open("/book", "_blank")}
                      >
                        <ExternalLink className="w-4 h-4 mr-2" />
                        Open Chatbot Page
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </motion.div>
      </div>

      <div className="noise-overlay" />
    </div>
  );
}
