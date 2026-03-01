import { useState, useEffect } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Users,
  CalendarCheck,
  DoorOpen,
  Clock,
  Download,
  LogOut,
  LayoutDashboard,
  FileSpreadsheet,
  Eye,
  CheckCircle,
  XCircle,
  Receipt,
  ClipboardList,
  Pencil,
  Trash2,
  Image,
  FileText,
  Plus,
  Bed,
  Filter,
  X,
  FileDown,
  Settings,
  Key,
  Mail,
  Globe,
  Save
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminDashboard() {
  const [stats, setStats] = useState({
    total_guests: 0,
    total_checkins: 0,
    active_stays: 0,
    completed_stays: 0
  });
  const [records, setRecords] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSignature, setSelectedSignature] = useState(null);
  const [activeView, setActiveView] = useState("dashboard");
  const [editingRecord, setEditingRecord] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  
  // Date filter state
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [isFiltered, setIsFiltered] = useState(false);
  
  // Room management state
  const [showRoomDialog, setShowRoomDialog] = useState(false);
  const [editingRoom, setEditingRoom] = useState(null);
  const [roomForm, setRoomForm] = useState({
    room_number: "",
    room_type: "Standard",
    floor: "1",
    notes: ""
  });
  const [deleteRoomConfirm, setDeleteRoomConfirm] = useState(null);
  
  // Portal Settings state
  const [portalSettings, setPortalSettings] = useState({
    api_global_username: "",
    api_global_password: "",
    alert_email: "",
    auto_sync_enabled: false,
    api_global_password_set: false
  });
  const [savingSettings, setSavingSettings] = useState(false);
  const [syncStatus, setSyncStatus] = useState({ running: false, progress: "", last_results: null });
  const [runningSyncTest, setRunningSyncTest] = useState(false);
  
  const navigate = useNavigate();

  useEffect(() => {
    const isAuth = sessionStorage.getItem("adminAuth");
    if (!isAuth) {
      navigate("/admin");
      return;
    }
    fetchData();
    fetchRooms();
    fetchSettings();
  }, [navigate]);

  const fetchData = async (filterStart = null, filterEnd = null) => {
    try {
      let recordsUrl = `${API}/admin/records`;
      const params = new URLSearchParams();
      if (filterStart) params.append('start_date', filterStart);
      if (filterEnd) params.append('end_date', filterEnd);
      if (params.toString()) recordsUrl += `?${params.toString()}`;
      
      const [statsRes, recordsRes] = await Promise.all([
        axios.get(`${API}/admin/stats`),
        axios.get(recordsUrl)
      ]);
      setStats(statsRes.data);
      setRecords(recordsRes.data);
    } catch (error) {
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const fetchRooms = async () => {
    try {
      const response = await axios.get(`${API}/admin/rooms`);
      setRooms(response.data);
    } catch (error) {
      console.error("Failed to load rooms");
    }
  };

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/admin/settings`);
      setPortalSettings({
        api_global_username: response.data.api_global_username || "",
        api_global_password: "",
        alert_email: response.data.alert_email || "",
        auto_sync_enabled: response.data.auto_sync_enabled || false,
        api_global_password_set: response.data.api_global_password_set || false
      });
    } catch (error) {
      console.error("Failed to load settings");
    }
  };

  const handleSaveSettings = async () => {
    setSavingSettings(true);
    try {
      await axios.post(`${API}/admin/settings`, {
        api_global_username: portalSettings.api_global_username,
        api_global_password: portalSettings.api_global_password || null,
        alert_email: portalSettings.alert_email,
        auto_sync_enabled: portalSettings.auto_sync_enabled
      });
      toast.success("Settings saved successfully");
      fetchSettings();
    } catch (error) {
      toast.error("Failed to save settings");
    } finally {
      setSavingSettings(false);
    }
  };

  const handleApplyFilter = () => {
    if (startDate || endDate) {
      setIsFiltered(true);
      fetchData(startDate, endDate);
      toast.success("Filter applied");
    }
  };

  const handleClearFilter = () => {
    setStartDate("");
    setEndDate("");
    setIsFiltered(false);
    fetchData();
    toast.success("Filter cleared");
  };

  const handleTestConnection = async () => {
    setRunningSyncTest(true);
    try {
      const response = await axios.post(`${API}/admin/settings/test-connection`);
      if (response.data.success) {
        toast.success(response.data.message);
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Connection test failed");
    } finally {
      setRunningSyncTest(false);
    }
  };

  const handleRunSync = async () => {
    try {
      const response = await axios.post(`${API}/admin/sync/run`);
      toast.success(`Sync started! Processing ${response.data.hodler_records_count} records...`);
      setSyncStatus({ ...syncStatus, running: true, progress: "Starting..." });
      
      // Poll for status
      const pollStatus = setInterval(async () => {
        try {
          const statusRes = await axios.get(`${API}/admin/sync/status`);
          setSyncStatus(statusRes.data);
          if (!statusRes.data.running) {
            clearInterval(pollStatus);
            if (statusRes.data.last_results) {
              const results = statusRes.data.last_results;
              toast.success(`Sync completed! Verified: ${results.verified?.length || 0}, No Bill: ${results.no_bill?.length || 0}`);
            }
          }
        } catch (e) {
          clearInterval(pollStatus);
        }
      }, 2000);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to start sync");
    }
  };

  const handleExportSignIn = async () => {
    try {
      const response = await axios.get(`${API}/admin/export`, {
        responseType: "blob"
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "hodler_inn_sign_in_sheet.xlsx");
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success("Sign-In Sheet (Excel) exported!");
    } catch (error) {
      toast.error("Failed to export");
    }
  };

  const handleExportSignInPng = async () => {
    try {
      const response = await axios.get(`${API}/admin/export-png`, {
        responseType: "blob"
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "hodler_inn_sign_in_sheet.png");
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success("Sign-In Sheet (PNG) exported!");
    } catch (error) {
      toast.error("Failed to export");
    }
  };

  const handleExportBilling = async () => {
    try {
      const response = await axios.get(`${API}/admin/export-billing`, {
        responseType: "blob"
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "hodler_inn_billing_report.xlsx");
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success("Billing Report (Excel) exported!");
    } catch (error) {
      toast.error("Failed to export");
    }
  };

  const handleExportBillingPng = async () => {
    try {
      const response = await axios.get(`${API}/admin/export-billing-png`, {
        responseType: "blob"
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "hodler_inn_billing_report.png");
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success("Billing Report (PNG) exported!");
    } catch (error) {
      toast.error("Failed to export");
    }
  };

  // PDF Export functions
  const handleExportSignInPdf = async () => {
    try {
      let url = `${API}/admin/export-pdf`;
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (params.toString()) url += `?${params.toString()}`;
      
      const response = await axios.get(url, { responseType: "blob" });
      const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = blobUrl;
      link.setAttribute("download", "hodler_inn_sign_in_sheet.pdf");
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(blobUrl);
      toast.success("Sign-In Sheet (PDF) exported!");
    } catch (error) {
      toast.error("Failed to export PDF");
    }
  };

  const handleExportBillingPdf = async () => {
    try {
      let url = `${API}/admin/export-billing-pdf`;
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (params.toString()) url += `?${params.toString()}`;
      
      const response = await axios.get(url, { responseType: "blob" });
      const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = blobUrl;
      link.setAttribute("download", "hodler_inn_billing_report.pdf");
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(blobUrl);
      toast.success("Billing Report (PDF) exported!");
    } catch (error) {
      toast.error("Failed to export PDF");
    }
  };

  // Room management functions
  const handleCreateRoom = async () => {
    if (!roomForm.room_number) {
      toast.error("Room number is required");
      return;
    }
    try {
      await axios.post(`${API}/admin/rooms`, roomForm);
      toast.success("Room created successfully");
      setShowRoomDialog(false);
      setRoomForm({ room_number: "", room_type: "Standard", floor: "1", notes: "" });
      fetchRooms();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create room");
    }
  };

  const handleEditRoom = (room) => {
    setEditingRoom(room);
    setRoomForm({
      room_number: room.room_number,
      room_type: room.room_type,
      floor: room.floor,
      notes: room.notes || ""
    });
    setShowRoomDialog(true);
  };

  const handleUpdateRoom = async () => {
    try {
      await axios.put(`${API}/admin/rooms/${editingRoom.id}`, roomForm);
      toast.success("Room updated successfully");
      setShowRoomDialog(false);
      setEditingRoom(null);
      setRoomForm({ room_number: "", room_type: "Standard", floor: "1", notes: "" });
      fetchRooms();
    } catch (error) {
      toast.error("Failed to update room");
    }
  };

  const handleDeleteRoom = async (roomId) => {
    try {
      await axios.delete(`${API}/admin/rooms/${roomId}`);
      toast.success("Room deleted successfully");
      setDeleteRoomConfirm(null);
      fetchRooms();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to delete room");
    }
  };

  const handleLogout = () => {
    sessionStorage.removeItem("adminAuth");
    navigate("/admin");
  };

  const handleEdit = (record) => {
    setEditingRecord(record);
    setEditForm({
      room_number: record.room_number,
      check_in_date: record.check_in_date,
      check_in_time: record.check_in_time,
      check_out_date: record.check_out_date || "",
      check_out_time: record.check_out_time || ""
    });
  };

  const handleSaveEdit = async () => {
    try {
      await axios.put(`${API}/admin/bookings/${editingRecord.id}`, editForm);
      toast.success("Record updated successfully");
      setEditingRecord(null);
      fetchData();
    } catch (error) {
      toast.error("Failed to update record");
    }
  };

  const handleDelete = async (bookingId) => {
    try {
      await axios.delete(`${API}/admin/bookings/${bookingId}`);
      toast.success("Record deleted successfully");
      setDeleteConfirm(null);
      fetchData();
    } catch (error) {
      toast.error("Failed to delete record");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-vault-bg flex items-center justify-center">
        <div className="text-vault-gold font-mono">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-vault-bg grid-bg" data-testid="admin-dashboard">
      {/* Sidebar - Hidden on mobile */}
      <div className="fixed left-0 top-0 h-full w-60 admin-sidebar p-6 flex-col hidden md:flex">
        {/* Logo */}
        <div className="flex items-center gap-3 mb-10">
          <img 
            src="https://customer-assets.emergentagent.com/job_guest-hotel-mgmt/artifacts/56yphta2_17721406444867042425090808501904.jpg" 
            alt="Hodler Inn Logo" 
            className="w-12 h-12 rounded-lg object-cover"
          />
          <div>
            <h1 className="font-outfit font-bold text-vault-text text-lg tracking-tight">HODLER INN</h1>
            <p className="font-mono text-[9px] text-vault-gold uppercase tracking-widest">Admin Panel</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="space-y-2 flex-1">
          <div 
            className={`admin-nav-item cursor-pointer ${activeView === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveView('dashboard')}
          >
            <LayoutDashboard className="w-4 h-4" />
            <span className="font-manrope text-sm">Dashboard</span>
          </div>
          <div 
            className={`admin-nav-item cursor-pointer ${activeView === 'signin' ? 'active' : ''}`}
            onClick={() => setActiveView('signin')}
            data-testid="nav-signin-view-btn"
          >
            <ClipboardList className="w-4 h-4" />
            <span className="font-manrope text-sm">Sign-In Sheet</span>
          </div>
          <div 
            className={`admin-nav-item cursor-pointer ${activeView === 'billing' ? 'active' : ''}`}
            onClick={() => setActiveView('billing')}
            data-testid="nav-billing-view-btn"
          >
            <Receipt className="w-4 h-4" />
            <span className="font-manrope text-sm">Billing Report</span>
          </div>
          <div 
            className={`admin-nav-item cursor-pointer ${activeView === 'rooms' ? 'active' : ''}`}
            onClick={() => setActiveView('rooms')}
            data-testid="nav-rooms-view-btn"
          >
            <Bed className="w-4 h-4" />
            <span className="font-manrope text-sm">Room Management</span>
          </div>
          <div 
            className={`admin-nav-item cursor-pointer ${activeView === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveView('settings')}
            data-testid="nav-settings-view-btn"
          >
            <Settings className="w-4 h-4" />
            <span className="font-manrope text-sm">Portal Settings</span>
          </div>
        </nav>

        {/* Logout */}
        <button 
          onClick={handleLogout}
          className="admin-nav-item mt-auto text-vault-error hover:text-red-400"
          data-testid="logout-btn"
        >
          <LogOut className="w-4 h-4" />
          <span className="font-manrope text-sm">Logout</span>
        </button>
      </div>

      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 bg-vault-surface border-b border-vault-border p-4 z-10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img 
              src="https://customer-assets.emergentagent.com/job_guest-hotel-mgmt/artifacts/56yphta2_17721406444867042425090808501904.jpg" 
              alt="Hodler Inn Logo" 
              className="w-8 h-8 rounded-lg object-cover"
            />
            <span className="font-outfit font-bold text-vault-text">HODLER INN</span>
          </div>
          <button 
            onClick={handleLogout}
            className="text-vault-text-secondary hover:text-vault-gold"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
        {/* Mobile Nav Tabs */}
        <div className="flex gap-2 mt-3 overflow-x-auto">
          <button 
            onClick={() => setActiveView('dashboard')}
            className={`px-3 py-1.5 rounded text-xs font-medium whitespace-nowrap ${activeView === 'dashboard' ? 'bg-vault-gold text-black' : 'bg-vault-surface-highlight text-vault-text-secondary'}`}
          >
            Dashboard
          </button>
          <button 
            onClick={() => setActiveView('signin')}
            className={`px-3 py-1.5 rounded text-xs font-medium whitespace-nowrap ${activeView === 'signin' ? 'bg-vault-gold text-black' : 'bg-vault-surface-highlight text-vault-text-secondary'}`}
          >
            Sign-In Sheet
          </button>
          <button 
            onClick={() => setActiveView('billing')}
            className={`px-3 py-1.5 rounded text-xs font-medium whitespace-nowrap ${activeView === 'billing' ? 'bg-vault-gold text-black' : 'bg-vault-surface-highlight text-vault-text-secondary'}`}
          >
            Billing Report
          </button>
          <button 
            onClick={() => setActiveView('rooms')}
            className={`px-3 py-1.5 rounded text-xs font-medium whitespace-nowrap ${activeView === 'rooms' ? 'bg-vault-gold text-black' : 'bg-vault-surface-highlight text-vault-text-secondary'}`}
          >
            Rooms
          </button>
          <button 
            onClick={() => setActiveView('settings')}
            className={`px-3 py-1.5 rounded text-xs font-medium whitespace-nowrap ${activeView === 'settings' ? 'bg-vault-gold text-black' : 'bg-vault-surface-highlight text-vault-text-secondary'}`}
          >
            Settings
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="md:ml-60 p-4 md:p-8 pt-28 md:pt-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          {/* Dashboard View */}
          {activeView === 'dashboard' && (
            <>
              {/* Header */}
              <div className="mb-8">
                <div className="flex justify-between items-center">
                  <div>
                    <h1 className="font-outfit text-3xl font-bold text-vault-text tracking-tight">Dashboard</h1>
                    <p className="text-vault-text-secondary font-manrope mt-1">Manage guest check-ins and billing</p>
                  </div>
                </div>
              </div>

              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <StatCard 
                  icon={<Users className="w-6 h-6" />}
                  label="Total Guests"
                  value={stats.total_guests}
                  testId="stat-total-guests"
                />
                <StatCard 
                  icon={<CalendarCheck className="w-6 h-6" />}
                  label="Total Check-ins"
                  value={stats.total_checkins}
                  testId="stat-total-checkins"
                />
                <StatCard 
                  icon={<DoorOpen className="w-6 h-6" />}
                  label="Active Stays"
                  value={stats.active_stays}
                  testId="stat-active-stays"
                />
                <StatCard 
                  icon={<Clock className="w-6 h-6" />}
                  label="Completed Stays"
                  value={stats.completed_stays}
                  testId="stat-completed-stays"
                />
              </div>

              {/* Records Table */}
              <Card className="bg-vault-surface border-vault-border" data-testid="records-table-card">
                <CardHeader className="border-b border-vault-border">
                  <CardTitle className="font-outfit text-xl text-vault-text flex items-center gap-2">
                    <FileSpreadsheet className="w-5 h-5 text-vault-gold" />
                    Guest Records
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <ScrollArea className="h-[400px]">
                    <Table>
                      <TableHeader>
                        <TableRow className="table-header border-vault-border hover:bg-transparent">
                          <TableHead className="text-vault-gold">Employee ID</TableHead>
                          <TableHead className="text-vault-gold">Name</TableHead>
                          <TableHead className="text-vault-gold">Room</TableHead>
                          <TableHead className="text-vault-gold">Check-In</TableHead>
                          <TableHead className="text-vault-gold">Check-Out</TableHead>
                          <TableHead className="text-vault-gold">Hours</TableHead>
                          <TableHead className="text-vault-gold">Nights</TableHead>
                          <TableHead className="text-vault-gold">Status</TableHead>
                          <TableHead className="text-vault-gold">Signature</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {records.length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={9} className="text-center text-vault-text-secondary py-8">
                              No records found
                            </TableCell>
                          </TableRow>
                        ) : (
                          records.map((record) => (
                            <TableRow key={record.id} className="table-row border-vault-border" data-testid={`record-row-${record.id}`}>
                              <TableCell className="font-mono text-vault-text">{record.employee_number}</TableCell>
                              <TableCell className="text-vault-text">{record.employee_name}</TableCell>
                              <TableCell className="font-mono text-vault-gold">{record.room_number}</TableCell>
                              <TableCell className="text-vault-text-secondary text-sm">
                                <div>{record.check_in_date}</div>
                                <div className="text-xs">{record.check_in_time}</div>
                              </TableCell>
                              <TableCell className="text-vault-text-secondary text-sm">
                                {record.check_out_date ? (
                                  <>
                                    <div>{record.check_out_date}</div>
                                    <div className="text-xs">{record.check_out_time}</div>
                                  </>
                                ) : (
                                  <span className="text-vault-text-secondary">—</span>
                                )}
                              </TableCell>
                              <TableCell className="font-mono text-vault-text">
                                {record.total_hours !== null ? `${record.total_hours}h` : "—"}
                              </TableCell>
                              <TableCell className="font-mono text-vault-gold font-bold">
                                {record.total_nights !== null ? record.total_nights : "—"}
                              </TableCell>
                              <TableCell>
                                {record.is_checked_out ? (
                                  <span className="flex items-center gap-1 text-vault-success text-sm">
                                    <CheckCircle className="w-4 h-4" />
                                    Completed
                                  </span>
                                ) : (
                                  <span className="flex items-center gap-1 text-vault-gold text-sm">
                                    <XCircle className="w-4 h-4" />
                                    Active
                                  </span>
                                )}
                              </TableCell>
                              <TableCell>
                                <Dialog>
                                  <DialogTrigger asChild>
                                    <Button 
                                      variant="ghost" 
                                      size="sm"
                                      className="text-vault-text-secondary hover:text-vault-gold"
                                      onClick={() => setSelectedSignature(record.signature)}
                                      data-testid={`view-signature-${record.id}`}
                                    >
                                      <Eye className="w-4 h-4" />
                                    </Button>
                                  </DialogTrigger>
                                  <DialogContent className="bg-vault-surface border-vault-border">
                                    <DialogHeader>
                                      <DialogTitle className="font-outfit text-vault-text">
                                        Signature - {record.employee_name}
                                      </DialogTitle>
                                    </DialogHeader>
                                    <div className="bg-black/50 rounded-lg p-4">
                                      <img 
                                        src={record.signature} 
                                        alt="Signature"
                                        className="w-full h-40 object-contain"
                                      />
                                    </div>
                                  </DialogContent>
                                </Dialog>
                              </TableCell>
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </ScrollArea>
                </CardContent>
              </Card>
            </>
          )}

          {/* Sign-In Sheet View */}
          {activeView === 'signin' && (
            <>
              {/* Header */}
              <div className="mb-6">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div>
                    <h1 className="font-outfit text-3xl font-bold text-vault-text tracking-tight">Sign-In Sheet</h1>
                    <p className="text-vault-text-secondary font-manrope mt-1">View all guest sign-in records</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button 
                      onClick={handleExportSignIn}
                      className="vault-btn-primary flex items-center gap-2"
                      data-testid="export-signin-excel-btn"
                    >
                      <FileText className="w-4 h-4" />
                      Excel
                    </Button>
                    <Button 
                      onClick={handleExportSignInPng}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white flex items-center gap-2"
                      data-testid="export-signin-png-btn"
                    >
                      <Image className="w-4 h-4" />
                      PNG
                    </Button>
                    <Button 
                      onClick={handleExportSignInPdf}
                      className="bg-red-600 hover:bg-red-700 text-white flex items-center gap-2"
                      data-testid="export-signin-pdf-btn"
                    >
                      <FileDown className="w-4 h-4" />
                      PDF
                    </Button>
                  </div>
                </div>
                
                {/* Date Filter */}
                <div className="mt-4 flex flex-wrap items-center gap-3 bg-vault-surface-highlight/50 p-3 rounded-lg border border-vault-border">
                  <Filter className="w-4 h-4 text-vault-gold" />
                  <span className="text-vault-text-secondary text-sm font-medium">Filter:</span>
                  <Input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-40 bg-black/50 border-vault-border text-vault-text text-sm h-9"
                    placeholder="Start Date"
                    data-testid="filter-start-date"
                  />
                  <span className="text-vault-text-secondary">to</span>
                  <Input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-40 bg-black/50 border-vault-border text-vault-text text-sm h-9"
                    placeholder="End Date"
                    data-testid="filter-end-date"
                  />
                  <Button
                    onClick={handleApplyFilter}
                    className="vault-btn-primary h-9 px-4"
                    data-testid="apply-filter-btn"
                  >
                    Apply
                  </Button>
                  {isFiltered && (
                    <Button
                      onClick={handleClearFilter}
                      variant="ghost"
                      className="h-9 px-3 text-vault-text-secondary hover:text-vault-gold"
                      data-testid="clear-filter-btn"
                    >
                      <X className="w-4 h-4 mr-1" />
                      Clear
                    </Button>
                  )}
                </div>
              </div>

              {/* Company Header Card */}
              <Card className="bg-vault-surface border-vault-border mb-6" data-testid="signin-sheet-card">
                <CardHeader className="border-b border-vault-border text-center py-4">
                  <CardTitle className="font-outfit text-2xl text-vault-gold">Hodler Inn</CardTitle>
                  <p className="text-vault-text-secondary text-sm">820 Hwy 59 N Heavener, OK, 74937</p>
                  <p className="text-vault-text-secondary text-sm">Phone: 918-653-7801</p>
                </CardHeader>
                <CardContent className="p-0 overflow-x-auto">
                  <div className="min-w-[1200px]">
                    <Table>
                      <TableHeader>
                        <TableRow className="table-header border-vault-border hover:bg-transparent">
                          <TableHead className="text-vault-gold w-12">#</TableHead>
                          <TableHead className="text-vault-gold">Stay Type</TableHead>
                          <TableHead className="text-vault-gold">Name</TableHead>
                          <TableHead className="text-vault-gold">Employee ID</TableHead>
                          <TableHead className="text-vault-gold">Signature In</TableHead>
                          <TableHead className="text-vault-gold">Signature Out</TableHead>
                          <TableHead className="text-vault-gold">Date In</TableHead>
                          <TableHead className="text-vault-gold">Time In</TableHead>
                          <TableHead className="text-vault-gold">Date Out</TableHead>
                          <TableHead className="text-vault-gold">Time Out</TableHead>
                          <TableHead className="text-vault-gold">Room #</TableHead>
                          <TableHead className="text-vault-gold">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {records.length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={12} className="text-center text-vault-text-secondary py-8">
                              No records found
                            </TableCell>
                          </TableRow>
                        ) : (
                          records.map((record, index) => (
                            <TableRow key={record.id} className="table-row border-vault-border" data-testid={`signin-row-${record.id}`}>
                              <TableCell className="font-mono text-vault-text">{index + 1}</TableCell>
                              <TableCell className="text-vault-text">Single Stay</TableCell>
                              <TableCell className="text-vault-text font-medium">{record.employee_name}</TableCell>
                              <TableCell className="font-mono text-vault-text">{record.employee_number}</TableCell>
                              <TableCell>
                                {record.signature ? (
                                  <Dialog>
                                    <DialogTrigger asChild>
                                      <button className="flex items-center gap-1 text-vault-success hover:text-vault-gold transition-colors cursor-pointer">
                                        <img 
                                          src={record.signature} 
                                          alt="Signature" 
                                          className="w-12 h-8 object-contain bg-black/30 rounded border border-vault-border"
                                        />
                                      </button>
                                    </DialogTrigger>
                                    <DialogContent className="bg-vault-surface border-vault-border">
                                      <DialogHeader>
                                        <DialogTitle className="font-outfit text-vault-text">
                                          Signature - {record.employee_name}
                                        </DialogTitle>
                                      </DialogHeader>
                                      <div className="bg-black/50 rounded-lg p-4">
                                        <img 
                                          src={record.signature} 
                                          alt="Signature"
                                          className="w-full h-40 object-contain"
                                        />
                                      </div>
                                    </DialogContent>
                                  </Dialog>
                                ) : "—"}
                              </TableCell>
                              <TableCell>
                                {record.is_checked_out && record.signature ? (
                                  <Dialog>
                                    <DialogTrigger asChild>
                                      <button className="flex items-center gap-1 text-vault-success hover:text-vault-gold transition-colors cursor-pointer">
                                        <img 
                                          src={record.signature} 
                                          alt="Signature" 
                                          className="w-12 h-8 object-contain bg-black/30 rounded border border-vault-border"
                                        />
                                      </button>
                                    </DialogTrigger>
                                    <DialogContent className="bg-vault-surface border-vault-border">
                                      <DialogHeader>
                                        <DialogTitle className="font-outfit text-vault-text">
                                          Signature - {record.employee_name}
                                        </DialogTitle>
                                      </DialogHeader>
                                      <div className="bg-black/50 rounded-lg p-4">
                                        <img 
                                          src={record.signature} 
                                          alt="Signature"
                                          className="w-full h-40 object-contain"
                                        />
                                      </div>
                                    </DialogContent>
                                  </Dialog>
                                ) : "—"}
                              </TableCell>
                              <TableCell className="text-vault-text">{record.check_in_date}</TableCell>
                              <TableCell className="font-mono text-vault-text">{record.check_in_time}</TableCell>
                              <TableCell className="text-vault-text">{record.check_out_date || "—"}</TableCell>
                              <TableCell className="font-mono text-vault-text">{record.check_out_time || "—"}</TableCell>
                              <TableCell className="font-mono text-vault-gold font-bold">{record.room_number}</TableCell>
                              <TableCell>
                                <div className="flex gap-1">
                                  <Button 
                                    variant="ghost" 
                                    size="sm"
                                    className="text-vault-text-secondary hover:text-vault-gold h-8 w-8 p-0"
                                    onClick={() => handleEdit(record)}
                                    data-testid={`edit-${record.id}`}
                                  >
                                    <Pencil className="w-4 h-4" />
                                  </Button>
                                  <Button 
                                    variant="ghost" 
                                    size="sm"
                                    className="text-vault-text-secondary hover:text-red-500 h-8 w-8 p-0"
                                    onClick={() => setDeleteConfirm(record)}
                                    data-testid={`delete-${record.id}`}
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </Button>
                                </div>
                              </TableCell>
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
              
              {/* Mobile hint */}
              <p className="text-vault-text-secondary text-xs text-center md:hidden">
                ← Swipe table horizontally to see all columns →
              </p>
            </>
          )}

          {/* Billing Report View */}
          {activeView === 'billing' && (
            <>
              {/* Header */}
              <div className="mb-6">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div>
                    <h1 className="font-outfit text-3xl font-bold text-vault-text tracking-tight">Billing Report</h1>
                    <p className="text-vault-text-secondary font-manrope mt-1">View completed stays and billing details</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button 
                      onClick={handleExportBilling}
                      className="vault-btn-primary flex items-center gap-2"
                      data-testid="export-billing-excel-btn"
                    >
                      <FileText className="w-4 h-4" />
                      Excel
                    </Button>
                    <Button 
                      onClick={handleExportBillingPng}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white flex items-center gap-2"
                      data-testid="export-billing-png-btn"
                    >
                      <Image className="w-4 h-4" />
                      PNG
                    </Button>
                    <Button 
                      onClick={handleExportBillingPdf}
                      className="bg-red-600 hover:bg-red-700 text-white flex items-center gap-2"
                      data-testid="export-billing-pdf-btn"
                    >
                      <FileDown className="w-4 h-4" />
                      PDF
                    </Button>
                  </div>
                </div>
                
                {/* Date Filter */}
                <div className="mt-4 flex flex-wrap items-center gap-3 bg-vault-surface-highlight/50 p-3 rounded-lg border border-vault-border">
                  <Filter className="w-4 h-4 text-vault-gold" />
                  <span className="text-vault-text-secondary text-sm font-medium">Filter:</span>
                  <Input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-40 bg-black/50 border-vault-border text-vault-text text-sm h-9"
                    placeholder="Start Date"
                  />
                  <span className="text-vault-text-secondary">to</span>
                  <Input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-40 bg-black/50 border-vault-border text-vault-text text-sm h-9"
                    placeholder="End Date"
                  />
                  <Button
                    onClick={handleApplyFilter}
                    className="vault-btn-primary h-9 px-4"
                  >
                    Apply
                  </Button>
                  {isFiltered && (
                    <Button
                      onClick={handleClearFilter}
                      variant="ghost"
                      className="h-9 px-3 text-vault-text-secondary hover:text-vault-gold"
                    >
                      <X className="w-4 h-4 mr-1" />
                      Clear
                    </Button>
                  )}
                </div>
              </div>

              {/* Billing Summary */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <StatCard 
                  icon={<CheckCircle className="w-6 h-6" />}
                  label="Completed Stays"
                  value={records.filter(r => r.is_checked_out).length}
                  testId="billing-completed"
                />
                <StatCard 
                  icon={<Clock className="w-6 h-6" />}
                  label="Total Hours"
                  value={records.filter(r => r.is_checked_out).reduce((sum, r) => sum + (r.total_hours || 0), 0).toFixed(1) + "h"}
                  testId="billing-hours"
                />
                <StatCard 
                  icon={<Receipt className="w-6 h-6" />}
                  label="Total Nights Billed"
                  value={records.filter(r => r.is_checked_out).reduce((sum, r) => sum + (r.total_nights || 0), 0)}
                  testId="billing-nights"
                />
              </div>

              {/* Billing Table */}
              <Card className="bg-vault-surface border-vault-border" data-testid="billing-table-card">
                <CardHeader className="border-b border-vault-border">
                  <CardTitle className="font-outfit text-xl text-vault-text flex items-center gap-2">
                    <Receipt className="w-5 h-5 text-vault-gold" />
                    Billing Details
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <ScrollArea className="h-[400px]">
                    <Table>
                      <TableHeader>
                        <TableRow className="table-header border-vault-border hover:bg-transparent">
                          <TableHead className="text-vault-gold">#</TableHead>
                          <TableHead className="text-vault-gold">Name</TableHead>
                          <TableHead className="text-vault-gold">Employee ID</TableHead>
                          <TableHead className="text-vault-gold">Room #</TableHead>
                          <TableHead className="text-vault-gold">Check-In</TableHead>
                          <TableHead className="text-vault-gold">Check-Out</TableHead>
                          <TableHead className="text-vault-gold">Total Hours</TableHead>
                          <TableHead className="text-vault-gold">Nights Billed</TableHead>
                          <TableHead className="text-vault-gold">Signed</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {records.filter(r => r.is_checked_out).length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={9} className="text-center text-vault-text-secondary py-8">
                              No completed stays found
                            </TableCell>
                          </TableRow>
                        ) : (
                          records.filter(r => r.is_checked_out).map((record, index) => (
                            <TableRow key={record.id} className="table-row border-vault-border" data-testid={`billing-row-${record.id}`}>
                              <TableCell className="font-mono text-vault-text">{index + 1}</TableCell>
                              <TableCell className="text-vault-text font-medium">{record.employee_name}</TableCell>
                              <TableCell className="font-mono text-vault-text">{record.employee_number}</TableCell>
                              <TableCell className="font-mono text-vault-gold font-bold">{record.room_number}</TableCell>
                              <TableCell className="text-vault-text-secondary text-sm">
                                {record.check_in_date} {record.check_in_time}
                              </TableCell>
                              <TableCell className="text-vault-text-secondary text-sm">
                                {record.check_out_date} {record.check_out_time}
                              </TableCell>
                              <TableCell className="font-mono text-vault-text">{record.total_hours}h</TableCell>
                              <TableCell className="font-mono text-vault-gold font-bold text-lg">{record.total_nights}</TableCell>
                              <TableCell>
                                {record.signature ? (
                                  <Dialog>
                                    <DialogTrigger asChild>
                                      <button className="cursor-pointer">
                                        <img 
                                          src={record.signature} 
                                          alt="Signature" 
                                          className="w-16 h-10 object-contain bg-black/30 rounded border border-vault-border hover:border-vault-gold transition-colors"
                                        />
                                      </button>
                                    </DialogTrigger>
                                    <DialogContent className="bg-vault-surface border-vault-border">
                                      <DialogHeader>
                                        <DialogTitle className="font-outfit text-vault-text">
                                          Signature - {record.employee_name}
                                        </DialogTitle>
                                      </DialogHeader>
                                      <div className="bg-black/50 rounded-lg p-4">
                                        <img 
                                          src={record.signature} 
                                          alt="Signature"
                                          className="w-full h-40 object-contain"
                                        />
                                      </div>
                                    </DialogContent>
                                  </Dialog>
                                ) : (
                                  <span className="text-vault-text-secondary">No</span>
                                )}
                              </TableCell>
                            </TableRow>
                          ))
                        )}
                        {/* Total Row */}
                        {records.filter(r => r.is_checked_out).length > 0 && (
                          <TableRow className="bg-vault-surface-highlight border-vault-border">
                            <TableCell colSpan={6} className="text-right font-bold text-vault-text">
                              TOTAL
                            </TableCell>
                            <TableCell className="font-mono text-vault-text font-bold">
                              {records.filter(r => r.is_checked_out).reduce((sum, r) => sum + (r.total_hours || 0), 0).toFixed(1)}h
                            </TableCell>
                            <TableCell className="font-mono text-vault-gold font-bold text-lg">
                              {records.filter(r => r.is_checked_out).reduce((sum, r) => sum + (r.total_nights || 0), 0)}
                            </TableCell>
                            <TableCell></TableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </ScrollArea>
                </CardContent>
              </Card>
            </>
          )}

          {/* Room Management View */}
          {activeView === 'rooms' && (
            <>
              {/* Header with Add Room Button */}
              <div className="mb-6">
                <div className="flex flex-wrap justify-between items-start gap-4">
                  <div className="flex-1 min-w-0">
                    <h1 className="font-outfit text-3xl font-bold text-vault-text tracking-tight">Room Management</h1>
                    <p className="text-vault-text-secondary font-manrope mt-1">Add, edit, and manage hotel rooms</p>
                  </div>
                </div>
                {/* Add Room Button - Separate row for visibility */}
                <div className="mt-4">
                  <Button 
                    onClick={() => {
                      setEditingRoom(null);
                      setRoomForm({ room_number: "", room_type: "Standard", floor: "1", notes: "" });
                      setShowRoomDialog(true);
                    }}
                    className="vault-btn-primary flex items-center gap-2"
                    data-testid="add-room-btn"
                  >
                    <Plus className="w-4 h-4" />
                    Add Room
                  </Button>
                </div>
              </div>

              {/* Room Stats */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
                <StatCard 
                  icon={<Bed className="w-6 h-6" />}
                  label="Total Rooms"
                  value={rooms.length}
                  testId="stat-total-rooms"
                />
                <StatCard 
                  icon={<CheckCircle className="w-6 h-6" />}
                  label="Available"
                  value={rooms.filter(r => r.status === 'available').length}
                  testId="stat-available-rooms"
                />
                <StatCard 
                  icon={<DoorOpen className="w-6 h-6" />}
                  label="Occupied"
                  value={rooms.filter(r => r.status === 'occupied').length}
                  testId="stat-occupied-rooms"
                />
                <StatCard 
                  icon={<XCircle className="w-6 h-6" />}
                  label="Maintenance"
                  value={rooms.filter(r => r.status === 'maintenance').length}
                  testId="stat-maintenance-rooms"
                />
              </div>

              {/* Rooms Table */}
              <Card className="bg-vault-surface border-vault-border" data-testid="rooms-table-card">
                <CardHeader className="border-b border-vault-border">
                  <CardTitle className="font-outfit text-xl text-vault-text flex items-center gap-2">
                    <Bed className="w-5 h-5 text-vault-gold" />
                    All Rooms
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <ScrollArea className="h-[400px]">
                    <Table>
                      <TableHeader>
                        <TableRow className="table-header border-vault-border hover:bg-transparent">
                          <TableHead className="text-vault-gold">Room #</TableHead>
                          <TableHead className="text-vault-gold">Type</TableHead>
                          <TableHead className="text-vault-gold">Floor</TableHead>
                          <TableHead className="text-vault-gold">Status</TableHead>
                          <TableHead className="text-vault-gold">Notes</TableHead>
                          <TableHead className="text-vault-gold">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {rooms.length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={6} className="text-center text-vault-text-secondary py-8">
                              No rooms added yet. Click "Add Room" to get started.
                            </TableCell>
                          </TableRow>
                        ) : (
                          rooms.map((room) => (
                            <TableRow key={room.id} className="table-row border-vault-border" data-testid={`room-row-${room.id}`}>
                              <TableCell className="font-mono text-vault-gold font-bold">{room.room_number}</TableCell>
                              <TableCell className="text-vault-text">{room.room_type}</TableCell>
                              <TableCell className="text-vault-text">{room.floor}</TableCell>
                              <TableCell>
                                <span className={`px-2 py-1 rounded text-xs font-medium ${
                                  room.status === 'available' ? 'bg-green-500/20 text-green-400' :
                                  room.status === 'occupied' ? 'bg-amber-500/20 text-amber-400' :
                                  'bg-red-500/20 text-red-400'
                                }`}>
                                  {room.status.charAt(0).toUpperCase() + room.status.slice(1)}
                                </span>
                              </TableCell>
                              <TableCell className="text-vault-text-secondary text-sm">{room.notes || "-"}</TableCell>
                              <TableCell>
                                <div className="flex gap-1">
                                  <Button 
                                    variant="ghost" 
                                    size="sm"
                                    className="text-vault-text-secondary hover:text-vault-gold h-8 w-8 p-0"
                                    onClick={() => handleEditRoom(room)}
                                    data-testid={`edit-room-${room.id}`}
                                  >
                                    <Pencil className="w-4 h-4" />
                                  </Button>
                                  <Button 
                                    variant="ghost" 
                                    size="sm"
                                    className="text-vault-text-secondary hover:text-red-500 h-8 w-8 p-0"
                                    onClick={() => setDeleteRoomConfirm(room)}
                                    data-testid={`delete-room-${room.id}`}
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </Button>
                                </div>
                              </TableCell>
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </ScrollArea>
                </CardContent>
              </Card>
            </>
          )}

          {/* Settings View */}
          {activeView === 'settings' && (
            <>
              {/* Header */}
              <div className="mb-6">
                <h1 className="font-outfit text-3xl font-bold text-vault-text tracking-tight">Portal Settings</h1>
                <p className="text-vault-text-secondary font-manrope mt-1">Configure API Global portal integration for automated verification</p>
              </div>

              {/* Settings Card */}
              <Card className="bg-vault-surface border-vault-border max-w-2xl" data-testid="settings-card">
                <CardHeader className="border-b border-vault-border">
                  <CardTitle className="font-outfit text-xl text-vault-text flex items-center gap-2">
                    <Globe className="w-5 h-5 text-vault-gold" />
                    API Global Portal Credentials
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6 space-y-6">
                  {/* Username */}
                  <div>
                    <label className="text-xs text-vault-gold uppercase tracking-wider mb-2 block font-medium">
                      Portal Username
                    </label>
                    <div className="relative">
                      <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-vault-text-secondary" />
                      <Input
                        value={portalSettings.api_global_username}
                        onChange={(e) => setPortalSettings({...portalSettings, api_global_username: e.target.value})}
                        placeholder="Enter your API Global username"
                        className="bg-black/50 border-vault-border text-vault-text pl-10"
                        data-testid="portal-username-input"
                      />
                    </div>
                  </div>

                  {/* Password */}
                  <div>
                    <label className="text-xs text-vault-gold uppercase tracking-wider mb-2 block font-medium">
                      Portal Password
                      {portalSettings.api_global_password_set && (
                        <span className="text-green-400 ml-2 normal-case">(Password saved)</span>
                      )}
                    </label>
                    <div className="relative">
                      <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-vault-text-secondary" />
                      <Input
                        type="password"
                        value={portalSettings.api_global_password}
                        onChange={(e) => setPortalSettings({...portalSettings, api_global_password: e.target.value})}
                        placeholder={portalSettings.api_global_password_set ? "Enter new password to change" : "Enter your API Global password"}
                        className="bg-black/50 border-vault-border text-vault-text pl-10"
                        data-testid="portal-password-input"
                      />
                    </div>
                    <p className="text-vault-text-secondary text-xs mt-1">
                      Password is encrypted and stored securely. Leave blank to keep existing password.
                    </p>
                  </div>

                  {/* Alert Email */}
                  <div>
                    <label className="text-xs text-vault-gold uppercase tracking-wider mb-2 block font-medium">
                      Alert Email
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-vault-text-secondary" />
                      <Input
                        type="email"
                        value={portalSettings.alert_email}
                        onChange={(e) => setPortalSettings({...portalSettings, alert_email: e.target.value})}
                        placeholder="Enter email for sync alerts"
                        className="bg-black/50 border-vault-border text-vault-text pl-10"
                        data-testid="alert-email-input"
                      />
                    </div>
                    <p className="text-vault-text-secondary text-xs mt-1">
                      Receive notifications for missing records and sync status.
                    </p>
                  </div>

                  {/* Save Button */}
                  <div className="pt-4 border-t border-vault-border">
                    <Button
                      onClick={handleSaveSettings}
                      disabled={savingSettings}
                      className="vault-btn-primary flex items-center gap-2"
                      data-testid="save-settings-btn"
                    >
                      <Save className="w-4 h-4" />
                      {savingSettings ? "Saving..." : "Save Settings"}
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Info Box */}
              <Card className="bg-vault-surface-highlight/50 border-vault-border max-w-2xl mt-6">
                <CardContent className="p-6">
                  <h3 className="font-outfit text-lg font-bold text-vault-gold mb-3">How AI Verification Works</h3>
                  <ol className="text-vault-text-secondary text-sm space-y-2 list-decimal list-inside">
                    <li>AI agent logs into API Global portal with your credentials</li>
                    <li>Loads sign-in sheets for the correct date</li>
                    <li>Matches names with your Hodler Inn records</li>
                    <li>Auto-fills Employee ID and Room Number for each match</li>
                    <li>Marks "No Bill" for entries not in your records</li>
                    <li>Sends email alert for any missing records</li>
                  </ol>
                  <p className="text-vault-gold text-sm mt-4">
                    <strong>Coming Soon:</strong> Automated daily sync feature
                  </p>
                </CardContent>
              </Card>
            </>
          )}
        </motion.div>
      </div>
      
      {/* Edit Dialog */}
      {editingRecord && (
        <Dialog open={!!editingRecord} onOpenChange={() => setEditingRecord(null)}>
          <DialogContent className="bg-vault-surface border-vault-border">
            <DialogHeader>
              <DialogTitle className="font-outfit text-vault-text">
                Edit Record - {editingRecord.employee_name}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Room Number</label>
                <Input
                  value={editForm.room_number}
                  onChange={(e) => setEditForm({...editForm, room_number: e.target.value})}
                  className="bg-black/50 border-vault-border text-vault-text"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Check-In Date</label>
                  <Input
                    type="date"
                    value={editForm.check_in_date}
                    onChange={(e) => setEditForm({...editForm, check_in_date: e.target.value})}
                    className="bg-black/50 border-vault-border text-vault-text"
                  />
                </div>
                <div>
                  <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Check-In Time</label>
                  <Input
                    type="time"
                    value={editForm.check_in_time}
                    onChange={(e) => setEditForm({...editForm, check_in_time: e.target.value})}
                    className="bg-black/50 border-vault-border text-vault-text"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Check-Out Date</label>
                  <Input
                    type="date"
                    value={editForm.check_out_date}
                    onChange={(e) => setEditForm({...editForm, check_out_date: e.target.value})}
                    className="bg-black/50 border-vault-border text-vault-text"
                  />
                </div>
                <div>
                  <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Check-Out Time</label>
                  <Input
                    type="time"
                    value={editForm.check_out_time}
                    onChange={(e) => setEditForm({...editForm, check_out_time: e.target.value})}
                    className="bg-black/50 border-vault-border text-vault-text"
                  />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="ghost" onClick={() => setEditingRecord(null)} className="text-vault-text-secondary">
                Cancel
              </Button>
              <Button onClick={handleSaveEdit} className="vault-btn-primary">
                Save Changes
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* Delete Confirmation Dialog */}
      {deleteConfirm && (
        <Dialog open={!!deleteConfirm} onOpenChange={() => setDeleteConfirm(null)}>
          <DialogContent className="bg-vault-surface border-vault-border">
            <DialogHeader>
              <DialogTitle className="font-outfit text-vault-text">
                Delete Record
              </DialogTitle>
            </DialogHeader>
            <p className="text-vault-text-secondary py-4">
              Are you sure you want to delete the record for <span className="text-vault-gold font-medium">{deleteConfirm.employee_name}</span> in room <span className="text-vault-gold font-medium">{deleteConfirm.room_number}</span>?
            </p>
            <DialogFooter>
              <Button variant="ghost" onClick={() => setDeleteConfirm(null)} className="text-vault-text-secondary">
                Cancel
              </Button>
              <Button onClick={() => handleDelete(deleteConfirm.id)} className="bg-red-600 hover:bg-red-700 text-white">
                Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* Room Add/Edit Dialog */}
      {showRoomDialog && (
        <Dialog open={showRoomDialog} onOpenChange={() => { setShowRoomDialog(false); setEditingRoom(null); }}>
          <DialogContent className="bg-vault-surface border-vault-border">
            <DialogHeader>
              <DialogTitle className="font-outfit text-vault-text">
                {editingRoom ? 'Edit Room' : 'Add New Room'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Room Number *</label>
                <Input
                  value={roomForm.room_number}
                  onChange={(e) => setRoomForm({...roomForm, room_number: e.target.value})}
                  placeholder="e.g., 101, 102A"
                  className="bg-black/50 border-vault-border text-vault-text"
                  data-testid="room-number-input"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Room Type</label>
                  <Select value={roomForm.room_type} onValueChange={(v) => setRoomForm({...roomForm, room_type: v})}>
                    <SelectTrigger className="bg-black/50 border-vault-border text-vault-text">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-vault-surface border-vault-border">
                      <SelectItem value="Standard">Standard</SelectItem>
                      <SelectItem value="Deluxe">Deluxe</SelectItem>
                      <SelectItem value="Suite">Suite</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Floor</label>
                  <Select value={roomForm.floor} onValueChange={(v) => setRoomForm({...roomForm, floor: v})}>
                    <SelectTrigger className="bg-black/50 border-vault-border text-vault-text">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-vault-surface border-vault-border">
                      <SelectItem value="1">Floor 1</SelectItem>
                      <SelectItem value="2">Floor 2</SelectItem>
                      <SelectItem value="3">Floor 3</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              {editingRoom && (
                <div>
                  <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Status</label>
                  <Select value={roomForm.status || editingRoom.status} onValueChange={(v) => setRoomForm({...roomForm, status: v})}>
                    <SelectTrigger className="bg-black/50 border-vault-border text-vault-text">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-vault-surface border-vault-border">
                      <SelectItem value="available">Available</SelectItem>
                      <SelectItem value="maintenance">Maintenance</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}
              <div>
                <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Notes</label>
                <Input
                  value={roomForm.notes}
                  onChange={(e) => setRoomForm({...roomForm, notes: e.target.value})}
                  placeholder="Optional notes about the room"
                  className="bg-black/50 border-vault-border text-vault-text"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="ghost" onClick={() => { setShowRoomDialog(false); setEditingRoom(null); }} className="text-vault-text-secondary">
                Cancel
              </Button>
              <Button 
                onClick={editingRoom ? handleUpdateRoom : handleCreateRoom} 
                className="vault-btn-primary"
                data-testid="save-room-btn"
              >
                {editingRoom ? 'Save Changes' : 'Add Room'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* Delete Room Confirmation Dialog */}
      {deleteRoomConfirm && (
        <Dialog open={!!deleteRoomConfirm} onOpenChange={() => setDeleteRoomConfirm(null)}>
          <DialogContent className="bg-vault-surface border-vault-border">
            <DialogHeader>
              <DialogTitle className="font-outfit text-vault-text">
                Delete Room
              </DialogTitle>
            </DialogHeader>
            <p className="text-vault-text-secondary py-4">
              Are you sure you want to delete <span className="text-vault-gold font-medium">Room {deleteRoomConfirm.room_number}</span>? This action cannot be undone.
            </p>
            <DialogFooter>
              <Button variant="ghost" onClick={() => setDeleteRoomConfirm(null)} className="text-vault-text-secondary">
                Cancel
              </Button>
              <Button onClick={() => handleDeleteRoom(deleteRoomConfirm.id)} className="bg-red-600 hover:bg-red-700 text-white">
                Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      <div className="noise-overlay" />
    </div>
  );
}

function StatCard({ icon, label, value, testId }) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="stat-card rounded-lg"
      data-testid={testId}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="font-mono text-xs uppercase tracking-wider text-vault-gold/80 mb-2">{label}</p>
          <p className="font-outfit text-4xl font-bold text-vault-text">{value}</p>
        </div>
        <div className="text-vault-gold/50">{icon}</div>
      </div>
    </motion.div>
  );
}
