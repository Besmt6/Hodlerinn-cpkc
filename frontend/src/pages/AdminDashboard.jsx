import { useState, useEffect } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { DatePicker } from "@/components/ui/date-picker";
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
  Save,
  Volume2,
  VolumeX,
  UserCheck,
  Flag,
  RefreshCw,
  AlertCircle,
  Search,
  Copy,
  CheckCheck,
  Link,
  Shield,
  FileBarChart,
  Cloud,
  Upload,
  UserX
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
  const [showActiveOnly, setShowActiveOnly] = useState(true);  // Default to showing only active/in-house guests
  
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
  
  // Employee management state
  const [employees, setEmployees] = useState([]);
  const [employeeSortBy, setEmployeeSortBy] = useState('name'); // 'name', 'id', 'date'
  const [employeeSortOrder, setEmployeeSortOrder] = useState('asc'); // 'asc', 'desc'
  const [employeeSearch, setEmployeeSearch] = useState('');
  const [showEmployeeDialog, setShowEmployeeDialog] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [employeeForm, setEmployeeForm] = useState({
    employee_number: "",
    name: ""
  });
  const [deleteEmployeeConfirm, setDeleteEmployeeConfirm] = useState(null);
  const [bulkImportText, setBulkImportText] = useState("");
  const [showBulkImport, setShowBulkImport] = useState(false);
  const [collectingEmployees, setCollectingEmployees] = useState(false);
  
  // Guest management state (verification)
  const [registeredGuests, setRegisteredGuests] = useState([]);
  const [loadingGuests, setLoadingGuests] = useState(false);
  
  // Blocked rooms state (other guests)
  const [blockedRooms, setBlockedRooms] = useState([]);
  const [showBlockRoomDialog, setShowBlockRoomDialog] = useState(false);
  const [blockRoomForm, setBlockRoomForm] = useState({ room_number: "", guest_name: "", notes: "" });
  
  // Guarantee report state
  const [guaranteeReport, setGuaranteeReport] = useState(null);
  const [guaranteeLoading, setGuaranteeLoading] = useState(false);
  const [guaranteeDateRange, setGuaranteeDateRange] = useState({ start: "", end: "" });
  
  // Turned Away Guests state
  const [turnedAwayGuests, setTurnedAwayGuests] = useState([]);
  const [showTurnedAwayForm, setShowTurnedAwayForm] = useState(false);
  const [turnedAwayStats, setTurnedAwayStats] = useState({ total_lost_revenue: 0, single_bed_count: 0, double_bed_count: 0 });
  const [turnedAwayForm, setTurnedAwayForm] = useState({
    date: new Date().toISOString().split('T')[0],
    guest_name: "Walk-in Guest",
    bed_type: "single",
    room_price: 85.00,
    reason: "Holding rooms for CPKC",
    notes: ""
  });
  
  // Portal Settings state
  const [portalSettings, setPortalSettings] = useState({
    api_global_username: "",
    api_global_password: "",
    alert_email: "",
    auto_sync_enabled: false,
    auto_sync_start_date: "",
    api_global_password_set: false,
    voice_enabled: true,
    voice_volume: 1.0,
    voice_speed: 0.85,
    telegram_chat_id: "",
    public_api_key: "",
    nightly_rate: 75.0,
    email_reports_enabled: false,
    email_smtp_host: "smtp.zoho.com",
    email_smtp_port: 587,
    email_sender: "",
    email_password_set: false,
    email_recipient: "",
    email_report_time: "00:00"
  });
  const [savingSettings, setSavingSettings] = useState(false);
  const [testingEmail, setTestingEmail] = useState(false);
  const [testingZoho, setTestingZoho] = useState(false);
  const [uploadingZoho, setUploadingZoho] = useState(false);
  const [zohoUploadDate, setZohoUploadDate] = useState(new Date().toISOString().split('T')[0]);
  const [syncStatus, setSyncStatus] = useState({ running: false, progress: "", last_results: null });
  const [runningSyncTest, setRunningSyncTest] = useState(false);
  const [syncTargetDate, setSyncTargetDate] = useState("");
  
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
    fetchEmployees();
    fetchRegisteredGuests();
    fetchBlockedRooms();
  }, [navigate]);

  const fetchRegisteredGuests = async () => {
    setLoadingGuests(true);
    try {
      const response = await axios.get(`${API}/admin/guests`);
      setRegisteredGuests(response.data);
    } catch (error) {
      console.error("Failed to load registered guests");
    } finally {
      setLoadingGuests(false);
    }
  };

  const handleVerifyGuest = async (employeeNumber) => {
    try {
      await axios.post(`${API}/admin/guests/${employeeNumber}/verify`);
      toast.success("Guest verified!");
      fetchRegisteredGuests();
    } catch (error) {
      toast.error("Failed to verify guest");
    }
  };

  const handleFlagGuest = async (employeeNumber) => {
    try {
      await axios.post(`${API}/admin/guests/${employeeNumber}/flag`);
      toast.warning("Guest flagged for review");
      fetchRegisteredGuests();
    } catch (error) {
      toast.error("Failed to flag guest");
    }
  };

  const handleBulkVerifyAll = async () => {
    const pendingGuests = registeredGuests.filter(g => !g.is_verified);
    if (pendingGuests.length === 0) {
      toast.info("No pending guests to verify");
      return;
    }
    
    try {
      const employeeNumbers = pendingGuests.map(g => g.employee_number);
      await axios.post(`${API}/admin/guests/bulk-verify`, { employee_numbers: employeeNumbers });
      toast.success(`Verified ${pendingGuests.length} guests!`);
      fetchRegisteredGuests();
    } catch (error) {
      toast.error("Failed to bulk verify guests");
    }
  };

  // Blocked rooms functions (Other Guests)
  const fetchBlockedRooms = async () => {
    try {
      const response = await axios.get(`${API}/admin/rooms/blocked`);
      setBlockedRooms(response.data);
    } catch (error) {
      console.error("Failed to load blocked rooms");
    }
  };

  const handleBlockRoom = async () => {
    if (!blockRoomForm.room_number) {
      toast.error("Please select a room");
      return;
    }
    try {
      await axios.post(`${API}/admin/rooms/block`, {
        room_number: blockRoomForm.room_number,
        guest_name: blockRoomForm.guest_name || "Other Guest",
        notes: blockRoomForm.notes
      });
      toast.success(`Room ${blockRoomForm.room_number} blocked for other guest`);
      setShowBlockRoomDialog(false);
      setBlockRoomForm({ room_number: "", guest_name: "", notes: "" });
      fetchRooms();
      fetchBlockedRooms();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to block room");
    }
  };

  const handleUnblockRoom = async (roomNumber) => {
    try {
      await axios.post(`${API}/admin/rooms/unblock/${roomNumber}`);
      toast.success(`Room ${roomNumber} unblocked`);
      fetchRooms();
      fetchBlockedRooms();
    } catch (error) {
      toast.error("Failed to unblock room");
    }
  };

  const handleMarkRoomDirty = async (roomNumber) => {
    try {
      await axios.post(`${API}/admin/rooms/${roomNumber}/mark-dirty`);
      toast.success(`Room ${roomNumber} marked as dirty`);
      fetchRooms();
    } catch (error) {
      toast.error("Failed to update room status");
    }
  };

  const handleMarkRoomClean = async (roomNumber) => {
    try {
      await axios.post(`${API}/admin/rooms/${roomNumber}/mark-clean`);
      toast.success(`Room ${roomNumber} marked as clean`);
      fetchRooms();
    } catch (error) {
      toast.error("Failed to update room status");
    }
  };

  const fetchGuaranteeReport = async (startDate = "", endDate = "") => {
    setGuaranteeLoading(true);
    try {
      let url = `${API}/admin/guarantee-report`;
      const params = [];
      if (startDate) params.push(`start_date=${startDate}`);
      if (endDate) params.push(`end_date=${endDate}`);
      if (params.length > 0) url += `?${params.join('&')}`;
      
      const response = await axios.get(url);
      setGuaranteeReport(response.data);
    } catch (error) {
      toast.error("Failed to load guarantee report");
    } finally {
      setGuaranteeLoading(false);
    }
  };

  const downloadGuaranteeReport = async () => {
    try {
      let url = `${API}/admin/export-guarantee-report`;
      const params = [];
      if (guaranteeDateRange.start) params.push(`start_date=${guaranteeDateRange.start}`);
      if (guaranteeDateRange.end) params.push(`end_date=${guaranteeDateRange.end}`);
      if (params.length > 0) url += `?${params.join('&')}`;
      
      const response = await axios.get(url, { responseType: 'blob' });
      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = 'hodler_inn_guarantee_report.xlsx';
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      toast.success("Guarantee report downloaded!");
    } catch (error) {
      toast.error("Failed to download report");
    }
  };

  // Turned Away Guests functions
  const fetchTurnedAwayGuests = async () => {
    try {
      let url = `${API}/admin/turned-away`;
      const params = [];
      if (guaranteeDateRange.start) params.push(`start_date=${guaranteeDateRange.start}`);
      if (guaranteeDateRange.end) params.push(`end_date=${guaranteeDateRange.end}`);
      if (params.length > 0) url += `?${params.join('&')}`;
      
      const response = await axios.get(url);
      setTurnedAwayGuests(response.data.records || []);
      setTurnedAwayStats({
        total_lost_revenue: response.data.total_lost_revenue || 0,
        single_bed_count: response.data.single_bed_count || 0,
        double_bed_count: response.data.double_bed_count || 0
      });
    } catch (error) {
      console.error("Failed to fetch turned away guests:", error);
    }
  };

  const handleLogTurnedAway = async () => {
    try {
      await axios.post(`${API}/admin/turned-away`, turnedAwayForm);
      toast.success("Turned away guest logged successfully");
      setShowTurnedAwayForm(false);
      setTurnedAwayForm({
        date: new Date().toISOString().split('T')[0],
        guest_name: "Walk-in Guest",
        bed_type: "single",
        room_price: 85.00,
        reason: "Holding rooms for CPKC",
        notes: ""
      });
      fetchTurnedAwayGuests();
      fetchGuaranteeReport(guaranteeDateRange.start, guaranteeDateRange.end);
    } catch (error) {
      toast.error("Failed to log turned away guest");
    }
  };

  const handleDeleteTurnedAway = async (recordId) => {
    if (!confirm("Are you sure you want to delete this record?")) return;
    try {
      await axios.delete(`${API}/admin/turned-away/${recordId}`);
      toast.success("Record deleted");
      fetchTurnedAwayGuests();
      fetchGuaranteeReport(guaranteeDateRange.start, guaranteeDateRange.end);
    } catch (error) {
      toast.error("Failed to delete record");
    }
  };

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/admin/employees`);
      setEmployees(response.data);
    } catch (error) {
      console.error("Failed to load employees");
    }
  };

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

  // Employee CRUD functions
  const handleSaveEmployee = async () => {
    if (!employeeForm.employee_number || !employeeForm.name) {
      toast.error("Please fill in all fields");
      return;
    }
    
    try {
      if (editingEmployee) {
        // Use id if available, otherwise fallback to employee_number
        const employeeIdentifier = editingEmployee.id || editingEmployee.employee_number;
        await axios.put(`${API}/admin/employees/${employeeIdentifier}`, employeeForm);
        toast.success("Employee updated successfully");
      } else {
        await axios.post(`${API}/admin/employees`, employeeForm);
        toast.success("Employee added successfully");
      }
      setShowEmployeeDialog(false);
      setEditingEmployee(null);
      setEmployeeForm({ employee_number: "", name: "" });
      fetchEmployees();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to save employee");
    }
  };

  const handleEditEmployee = (employee) => {
    setEditingEmployee(employee);
    setEmployeeForm({
      employee_number: employee.employee_number,
      name: employee.name
    });
    setShowEmployeeDialog(true);
  };

  const handleDeleteEmployee = async (employeeId) => {
    try {
      await axios.delete(`${API}/admin/employees/${employeeId}`);
      toast.success("Employee deleted successfully");
      setDeleteEmployeeConfirm(null);
      fetchEmployees();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to delete employee");
    }
  };

  const handleBulkImport = async () => {
    if (!bulkImportText.trim()) {
      toast.error("Please enter employee data");
      return;
    }
    
    try {
      // Parse CSV/text format: "employee_number,name" or "employee_number name"
      const lines = bulkImportText.trim().split('\n');
      const employeesToImport = lines.map(line => {
        const parts = line.split(/[,\t]/).map(p => p.trim());
        if (parts.length >= 2) {
          return { employee_number: parts[0], name: parts[1] };
        }
        return null;
      }).filter(e => e !== null);
      
      if (employeesToImport.length === 0) {
        toast.error("No valid employee data found. Use format: ID,Name");
        return;
      }
      
      const response = await axios.post(`${API}/admin/employees/bulk`, employeesToImport);
      toast.success(response.data.message);
      setBulkImportText("");
      setShowBulkImport(false);
      fetchEmployees();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to import employees");
    }
  };

  const handleCollectFromPortal = async () => {
    setCollectingEmployees(true);
    try {
      toast.info("AI Agent is collecting employees from portal... This may take a minute.");
      const response = await axios.post(`${API}/admin/collect-employees`);
      if (response.data.success) {
        toast.success(response.data.message);
        fetchEmployees();
      } else {
        toast.error(response.data.message || "Failed to collect employees");
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to collect employees from portal");
    } finally {
      setCollectingEmployees(false);
    }
  };

  const handleImportFromGuests = async () => {
    try {
      toast.info("Importing employees from your guest records...");
      const response = await axios.post(`${API}/admin/import-from-guests`);
      if (response.data.success) {
        toast.success(response.data.message);
        fetchEmployees();
      } else {
        toast.error(response.data.message || "Failed to import employees");
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to import from guest records");
    }
  };

  const fetchSettings = async () => {
    try {
      const [settingsRes, syncStatusRes] = await Promise.all([
        axios.get(`${API}/admin/settings`),
        axios.get(`${API}/admin/sync/status`)
      ]);
      setPortalSettings({
        api_global_username: settingsRes.data.api_global_username || "",
        api_global_password: "",
        alert_email: settingsRes.data.alert_email || "",
        auto_sync_enabled: settingsRes.data.auto_sync_enabled || false,
        auto_sync_start_date: settingsRes.data.auto_sync_start_date || "",
        api_global_password_set: settingsRes.data.api_global_password_set || false,
        voice_enabled: settingsRes.data.voice_enabled !== false,
        voice_volume: settingsRes.data.voice_volume || 1.0,
        voice_speed: settingsRes.data.voice_speed || 0.85,
        telegram_chat_id: settingsRes.data.telegram_chat_id || "",
        public_api_key: settingsRes.data.public_api_key || "",
        nightly_rate: settingsRes.data.nightly_rate || 75.0,
        email_reports_enabled: settingsRes.data.email_reports_enabled || false,
        email_smtp_host: settingsRes.data.email_smtp_host || "smtp.zoho.com",
        email_smtp_port: settingsRes.data.email_smtp_port || 587,
        email_sender: settingsRes.data.email_sender || "",
        email_password: "",
        email_password_set: settingsRes.data.email_password_set || false,
        email_recipient: settingsRes.data.email_recipient || "",
        email_report_time: settingsRes.data.email_report_time || "00:00"
      });
      setSyncStatus(syncStatusRes.data);
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
        auto_sync_enabled: portalSettings.auto_sync_enabled,
        telegram_chat_id: portalSettings.telegram_chat_id,
        public_api_key: portalSettings.public_api_key,
        nightly_rate: portalSettings.nightly_rate
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
      // Build URL with optional date parameter
      let url = `${API}/admin/sync/run`;
      if (syncTargetDate) {
        url += `?target_date=${syncTargetDate}`;
      }
      const response = await axios.post(url);
      toast.success(`Sync started for ${syncTargetDate || 'default date'}! Processing ${response.data.hodler_records_count} records...`);
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
      let url = `${API}/admin/export-billing`;
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (params.toString()) url += `?${params.toString()}`;
      
      const response = await axios.get(url, {
        responseType: "blob"
      });
      const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = blobUrl;
      const filename = startDate || endDate 
        ? `hodler_inn_billing_${startDate || 'start'}_to_${endDate || 'end'}.xlsx`
        : "hodler_inn_billing_report.xlsx";
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(blobUrl);
      toast.success("Billing Report (Excel) exported!");
    } catch (error) {
      toast.error("Failed to export");
    }
  };

  const handleExportBillingPng = async () => {
    try {
      let url = `${API}/admin/export-billing-png`;
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (params.toString()) url += `?${params.toString()}`;
      
      const response = await axios.get(url, {
        responseType: "blob"
      });
      const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = blobUrl;
      const filename = startDate || endDate 
        ? `hodler_inn_billing_${startDate || 'start'}_to_${endDate || 'end'}.png`
        : "hodler_inn_billing_report.png";
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(blobUrl);
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
            className={`admin-nav-item cursor-pointer ${activeView === 'employees' ? 'active' : ''}`}
            onClick={() => setActiveView('employees')}
            data-testid="nav-employees-view-btn"
          >
            <Users className="w-4 h-4" />
            <span className="font-manrope text-sm">Employee List</span>
          </div>
          <div 
            className={`admin-nav-item cursor-pointer ${activeView === 'guests' ? 'active' : ''}`}
            onClick={() => setActiveView('guests')}
            data-testid="nav-guests-view-btn"
          >
            <UserCheck className="w-4 h-4" />
            <span className="font-manrope text-sm">Guest Verification</span>
          </div>
          <div 
            className={`admin-nav-item cursor-pointer ${activeView === 'guarantee' ? 'active' : ''}`}
            onClick={() => setActiveView('guarantee')}
            data-testid="nav-guarantee-view-btn"
          >
            <FileBarChart className="w-4 h-4" />
            <span className="font-manrope text-sm">Guarantee Report</span>
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
            onClick={() => setActiveView('guarantee')}
            className={`px-3 py-1.5 rounded text-xs font-medium whitespace-nowrap ${activeView === 'guarantee' ? 'bg-vault-gold text-black' : 'bg-vault-surface-highlight text-vault-text-secondary'}`}
          >
            Guarantee
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
                  
                  {/* Active Only Toggle */}
                  <div className="flex items-center gap-2 bg-black/30 px-3 py-1.5 rounded-lg border border-vault-border">
                    <label className="text-vault-text-secondary text-sm cursor-pointer flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={showActiveOnly}
                        onChange={(e) => setShowActiveOnly(e.target.checked)}
                        className="w-4 h-4 accent-vault-gold cursor-pointer"
                        data-testid="show-active-only-toggle"
                      />
                      <span className={showActiveOnly ? "text-vault-gold font-medium" : ""}>
                        In-House Only
                      </span>
                    </label>
                  </div>
                  
                  <div className="h-6 w-px bg-vault-border mx-1" />
                  
                  <DatePicker
                    date={startDate}
                    onDateChange={setStartDate}
                    placeholder="Start Date"
                    className="h-9"
                  />
                  <span className="text-vault-text-secondary">to</span>
                  <DatePicker
                    date={endDate}
                    onDateChange={setEndDate}
                    placeholder="End Date"
                    className="h-9"
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
                
                {/* Active guests summary */}
                {showActiveOnly && (
                  <div className="mt-2 text-sm text-vault-text-secondary">
                    Showing <span className="text-vault-gold font-medium">{records.filter(r => !r.is_checked_out).length}</span> in-house guests 
                    (checked in but not checked out)
                  </div>
                )}
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
                        {(() => {
                          const filteredRecords = showActiveOnly 
                            ? records.filter(r => !r.is_checked_out) 
                            : records;
                          
                          if (filteredRecords.length === 0) {
                            return (
                              <TableRow>
                                <TableCell colSpan={12} className="text-center text-vault-text-secondary py-8">
                                  {showActiveOnly ? "No in-house guests found" : "No records found"}
                                </TableCell>
                              </TableRow>
                            );
                          }
                          
                          return filteredRecords.map((record, index) => (
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
                          ));
                        })()}
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
                  <DatePicker
                    date={startDate}
                    onDateChange={setStartDate}
                    placeholder="Start Date"
                    className="h-9"
                  />
                  <span className="text-vault-text-secondary">to</span>
                  <DatePicker
                    date={endDate}
                    onDateChange={setEndDate}
                    placeholder="End Date"
                    className="h-9"
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
                          <TableHead className="text-vault-gold">Actions</TableHead>
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
                              <TableCell>
                                <div className="flex items-center gap-2">
                                  <button
                                    onClick={() => handleEdit(record)}
                                    className="p-1.5 rounded hover:bg-vault-surface-highlight text-vault-text-secondary hover:text-vault-gold transition-colors"
                                    title="Edit record"
                                    data-testid={`billing-edit-${record.id}`}
                                  >
                                    <Pencil className="w-4 h-4" />
                                  </button>
                                </div>
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
                <div className="mt-4 flex gap-2">
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
                  <Button 
                    onClick={() => setShowBlockRoomDialog(true)}
                    className="bg-amber-600 hover:bg-amber-700 text-white flex items-center gap-2"
                    data-testid="block-room-btn"
                  >
                    <Users className="w-4 h-4" />
                    Block Room (Other Guest)
                  </Button>
                </div>
              </div>

              {/* Room Stats */}
              <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
                <StatCard 
                  icon={<Bed className="w-6 h-6" />}
                  label="Total Rooms"
                  value={rooms.length}
                  testId="stat-total-rooms"
                />
                <StatCard 
                  icon={<CheckCircle className="w-6 h-6" />}
                  label="Available"
                  value={rooms.filter(r => r.status === 'available').length - blockedRooms.length}
                  testId="stat-available-rooms"
                />
                <StatCard 
                  icon={<DoorOpen className="w-6 h-6" />}
                  label="Railroad Guests"
                  value={rooms.filter(r => r.status === 'occupied').length}
                  testId="stat-occupied-rooms"
                />
                <StatCard 
                  icon={<Users className="w-6 h-6" />}
                  label="Other Guests"
                  value={blockedRooms.length}
                  testId="stat-blocked-rooms"
                />
                <StatCard 
                  icon={<AlertCircle className="w-6 h-6" />}
                  label="Dirty"
                  value={rooms.filter(r => r.status === 'dirty').length}
                  testId="stat-dirty-rooms"
                />
                <StatCard 
                  icon={<XCircle className="w-6 h-6" />}
                  label="Maintenance"
                  value={rooms.filter(r => r.status === 'maintenance').length}
                  testId="stat-maintenance-rooms"
                />
              </div>

              {/* Blocked Rooms (Other Guests) Section */}
              {blockedRooms.length > 0 && (
                <Card className="bg-amber-900/20 border-amber-600/50 mb-6">
                  <CardHeader className="border-b border-amber-600/30 pb-3">
                    <CardTitle className="font-outfit text-lg text-amber-400 flex items-center gap-2">
                      <Users className="w-5 h-5" />
                      Blocked Rooms (Other Guests) - Not Billed to Railroad
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                      {blockedRooms.map((block) => (
                        <div key={block.id} className="bg-black/30 border border-amber-600/30 rounded-lg p-3 flex justify-between items-center">
                          <div>
                            <p className="text-amber-400 font-bold">Room {block.room_number}</p>
                            <p className="text-vault-text-secondary text-sm">{block.guest_name}</p>
                            {block.notes && <p className="text-vault-text-secondary text-xs">{block.notes}</p>}
                          </div>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-red-400 hover:text-red-300 hover:bg-red-900/30"
                            onClick={() => handleUnblockRoom(block.room_number)}
                            data-testid={`unblock-room-${block.room_number}`}
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

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
                                  room.status === 'dirty' ? 'bg-orange-500/20 text-orange-400' :
                                  'bg-red-500/20 text-red-400'
                                }`}>
                                  {room.status === 'available' ? 'Clean' : room.status.charAt(0).toUpperCase() + room.status.slice(1)}
                                </span>
                              </TableCell>
                              <TableCell className="text-vault-text-secondary text-sm">{room.notes || "-"}</TableCell>
                              <TableCell>
                                <div className="flex gap-1">
                                  {/* Quick dirty/clean toggle */}
                                  {room.status === 'dirty' && (
                                    <Button 
                                      variant="ghost" 
                                      size="sm"
                                      className="text-green-400 hover:text-green-300 hover:bg-green-900/30 h-8 px-2"
                                      onClick={() => handleMarkRoomClean(room.room_number)}
                                      title="Mark as Clean"
                                    >
                                      <CheckCircle className="w-4 h-4" />
                                    </Button>
                                  )}
                                  {room.status === 'available' && (
                                    <Button 
                                      variant="ghost" 
                                      size="sm"
                                      className="text-orange-400 hover:text-orange-300 hover:bg-orange-900/30 h-8 px-2"
                                      onClick={() => handleMarkRoomDirty(room.room_number)}
                                      title="Mark as Dirty"
                                    >
                                      <AlertCircle className="w-4 h-4" />
                                    </Button>
                                  )}
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

          {/* Employee List View */}
          {activeView === 'employees' && (
            <>
              {/* Header */}
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h1 className="font-outfit text-3xl font-bold text-vault-text tracking-tight">Employee List</h1>
                  <p className="text-vault-text-secondary font-manrope mt-1">Manage authorized employees who can check in</p>
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={async () => {
                      try {
                        const res = await axios.post(`${API}/admin/employees/sync-names-to-guests`);
                        toast.success(res.data.message);
                      } catch (error) {
                        toast.error("Failed to sync names");
                      }
                    }}
                    className="bg-amber-600 hover:bg-amber-700 text-white"
                    data-testid="sync-names-to-guests-btn"
                    title="Update guest records with current employee names (for sync agent)"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Sync Names to Guests
                  </Button>
                  <Button
                    onClick={handleImportFromGuests}
                    disabled={collectingEmployees}
                    className="bg-green-600 hover:bg-green-700 text-white"
                    data-testid="import-from-guests-btn"
                  >
                    <Users className="w-4 h-4 mr-2" />
                    Import from Guest Records
                  </Button>
                  <Button
                    onClick={handleCollectFromPortal}
                    disabled={collectingEmployees}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                    data-testid="collect-from-portal-btn"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    {collectingEmployees ? "Collecting..." : "Import from Portal"}
                  </Button>
                  <Button
                    onClick={() => setShowBulkImport(true)}
                    className="bg-vault-surface border border-vault-border hover:bg-vault-surface-highlight text-vault-text"
                    data-testid="bulk-import-employees-btn"
                  >
                    <FileSpreadsheet className="w-4 h-4 mr-2" />
                    Bulk Import
                  </Button>
                  <Button
                    onClick={() => {
                      setEditingEmployee(null);
                      setEmployeeForm({ employee_number: "", name: "" });
                      setShowEmployeeDialog(true);
                    }}
                    className="vault-btn-primary"
                    data-testid="add-employee-btn"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Add Employee
                  </Button>
                </div>
              </div>

              {/* Employee Stats */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <Card className="bg-vault-surface border-vault-border">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-vault-gold/20 rounded-lg">
                        <Users className="w-5 h-5 text-vault-gold" />
                      </div>
                      <div>
                        <p className="text-vault-text-secondary text-sm">Total Employees</p>
                        <p className="text-2xl font-bold text-vault-text font-mono">{employees.length}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-vault-surface border-vault-border">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-green-500/20 rounded-lg">
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      </div>
                      <div>
                        <p className="text-vault-text-secondary text-sm">Active Employees</p>
                        <p className="text-2xl font-bold text-vault-text font-mono">{employees.filter(e => e.is_active !== false).length}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Employee Table */}
              <Card className="bg-vault-surface border-vault-border">
                <CardHeader className="border-b border-vault-border">
                  <div className="flex items-center justify-between">
                    <CardTitle className="font-outfit text-xl text-vault-text flex items-center gap-2">
                      <Users className="w-5 h-5 text-vault-gold" />
                      All Employees
                    </CardTitle>
                    <div className="flex items-center gap-3">
                      {/* Search */}
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-vault-text-secondary" />
                        <Input
                          placeholder="Search by name or ID..."
                          value={employeeSearch}
                          onChange={(e) => setEmployeeSearch(e.target.value)}
                          className="pl-9 w-48 bg-black/50 border-vault-border text-vault-text text-sm"
                          data-testid="employee-search-input"
                        />
                      </div>
                      {/* Sort Options */}
                      <div className="flex items-center gap-1 text-sm">
                        <span className="text-vault-text-secondary">Sort:</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            if (employeeSortBy === 'name') {
                              setEmployeeSortOrder(employeeSortOrder === 'asc' ? 'desc' : 'asc');
                            } else {
                              setEmployeeSortBy('name');
                              setEmployeeSortOrder('asc');
                            }
                          }}
                          className={`text-xs px-2 ${employeeSortBy === 'name' ? 'text-vault-gold' : 'text-vault-text-secondary'}`}
                          data-testid="sort-by-name-btn"
                        >
                          A-Z {employeeSortBy === 'name' && (employeeSortOrder === 'asc' ? '↑' : '↓')}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            if (employeeSortBy === 'id') {
                              setEmployeeSortOrder(employeeSortOrder === 'asc' ? 'desc' : 'asc');
                            } else {
                              setEmployeeSortBy('id');
                              setEmployeeSortOrder('asc');
                            }
                          }}
                          className={`text-xs px-2 ${employeeSortBy === 'id' ? 'text-vault-gold' : 'text-vault-text-secondary'}`}
                          data-testid="sort-by-id-btn"
                        >
                          ID {employeeSortBy === 'id' && (employeeSortOrder === 'asc' ? '↑' : '↓')}
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <ScrollArea className="h-[400px]">
                    <Table>
                      <TableHeader>
                        <TableRow className="table-header border-vault-border hover:bg-transparent">
                          <TableHead className="text-vault-gold">Employee ID</TableHead>
                          <TableHead className="text-vault-gold">Name</TableHead>
                          <TableHead className="text-vault-gold">Status</TableHead>
                          <TableHead className="text-vault-gold">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {(() => {
                          // Filter employees
                          let filteredEmployees = employees.filter(emp => {
                            if (!employeeSearch) return true;
                            const search = employeeSearch.toLowerCase();
                            return (
                              (emp.name || '').toLowerCase().includes(search) ||
                              (emp.employee_number || '').toLowerCase().includes(search)
                            );
                          });
                          
                          // Sort employees
                          filteredEmployees = [...filteredEmployees].sort((a, b) => {
                            let aVal, bVal;
                            if (employeeSortBy === 'name') {
                              aVal = (a.name || '').toLowerCase();
                              bVal = (b.name || '').toLowerCase();
                            } else {
                              aVal = (a.employee_number || '').toLowerCase();
                              bVal = (b.employee_number || '').toLowerCase();
                            }
                            if (employeeSortOrder === 'asc') {
                              return aVal.localeCompare(bVal);
                            } else {
                              return bVal.localeCompare(aVal);
                            }
                          });
                          
                          if (filteredEmployees.length === 0) {
                            return (
                              <TableRow>
                                <TableCell colSpan={4} className="text-center text-vault-text-secondary py-8">
                                  {employeeSearch ? `No employees matching "${employeeSearch}"` : 'No employees added yet. Click "Add Employee" or "Bulk Import" to get started.'}
                                </TableCell>
                              </TableRow>
                            );
                          }
                          
                          return filteredEmployees.map((emp) => (
                            <TableRow key={emp.id} className="table-row border-vault-border" data-testid={`employee-row-${emp.id}`}>
                              <TableCell className="font-mono text-vault-gold font-bold">{emp.employee_number}</TableCell>
                              <TableCell className="text-vault-text">{emp.name}</TableCell>
                              <TableCell>
                                <span className={`px-2 py-1 rounded text-xs font-medium ${
                                  emp.is_active !== false ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                                }`}>
                                  {emp.is_active !== false ? 'Active' : 'Inactive'}
                                </span>
                              </TableCell>
                              <TableCell>
                                <div className="flex gap-1">
                                  <Button 
                                    variant="ghost" 
                                    size="sm"
                                    className="text-vault-text-secondary hover:text-vault-gold h-8 w-8 p-0"
                                    onClick={() => handleEditEmployee(emp)}
                                    data-testid={`edit-employee-${emp.id}`}
                                  >
                                    <Pencil className="w-4 h-4" />
                                  </Button>
                                  <Button 
                                    variant="ghost" 
                                    size="sm"
                                    className="text-vault-text-secondary hover:text-red-500 h-8 w-8 p-0"
                                    onClick={() => setDeleteEmployeeConfirm(emp)}
                                    data-testid={`delete-employee-${emp.id}`}
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </Button>
                                </div>
                              </TableCell>
                            </TableRow>
                          ));
                        })()}
                      </TableBody>
                    </Table>
                  </ScrollArea>
                </CardContent>
              </Card>

              {/* Add/Edit Employee Dialog */}
              <Dialog open={showEmployeeDialog} onOpenChange={setShowEmployeeDialog}>
                <DialogContent className="bg-vault-surface border-vault-border">
                  <DialogHeader>
                    <DialogTitle className="font-outfit text-vault-text">
                      {editingEmployee ? 'Edit Employee' : 'Add New Employee'}
                    </DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div>
                      <label className="text-sm text-vault-text-secondary mb-2 block">Employee ID</label>
                      <Input
                        value={employeeForm.employee_number}
                        onChange={(e) => setEmployeeForm({...employeeForm, employee_number: e.target.value})}
                        placeholder="Enter employee ID"
                        className="vault-input"
                        data-testid="employee-id-input"
                      />
                    </div>
                    <div>
                      <label className="text-sm text-vault-text-secondary mb-2 block">Full Name</label>
                      <Input
                        value={employeeForm.name}
                        onChange={(e) => setEmployeeForm({...employeeForm, name: e.target.value})}
                        placeholder="Enter full name"
                        className="vault-input"
                        data-testid="employee-name-input"
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <DialogClose asChild>
                      <Button variant="ghost" className="text-vault-text-secondary">Cancel</Button>
                    </DialogClose>
                    <Button onClick={handleSaveEmployee} className="vault-btn-primary" data-testid="save-employee-btn">
                      {editingEmployee ? 'Update' : 'Add'} Employee
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>

              {/* Bulk Import Dialog */}
              <Dialog open={showBulkImport} onOpenChange={setShowBulkImport}>
                <DialogContent className="bg-vault-surface border-vault-border max-w-lg">
                  <DialogHeader>
                    <DialogTitle className="font-outfit text-vault-text">Bulk Import Employees</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <p className="text-sm text-vault-text-secondary">
                      Enter employee data, one per line in format: <code className="text-vault-gold">ID,Name</code>
                    </p>
                    <textarea
                      value={bulkImportText}
                      onChange={(e) => setBulkImportText(e.target.value)}
                      placeholder="EMP001,John Smith&#10;EMP002,Jane Doe&#10;EMP003,Bob Wilson"
                      className="w-full h-40 p-3 vault-input font-mono text-sm resize-none"
                      data-testid="bulk-import-textarea"
                    />
                    <p className="text-xs text-vault-text-secondary">
                      Duplicate employee IDs will be skipped automatically.
                    </p>
                  </div>
                  <DialogFooter>
                    <DialogClose asChild>
                      <Button variant="ghost" className="text-vault-text-secondary">Cancel</Button>
                    </DialogClose>
                    <Button onClick={handleBulkImport} className="vault-btn-primary" data-testid="import-employees-btn">
                      Import Employees
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>

              {/* Delete Employee Confirmation */}
              <Dialog open={!!deleteEmployeeConfirm} onOpenChange={() => setDeleteEmployeeConfirm(null)}>
                <DialogContent className="bg-vault-surface border-vault-border">
                  <DialogHeader>
                    <DialogTitle className="font-outfit text-vault-text">Delete Employee</DialogTitle>
                  </DialogHeader>
                  <p className="text-vault-text-secondary">
                    Are you sure you want to delete employee <span className="text-vault-gold font-mono">{deleteEmployeeConfirm?.employee_number}</span> ({deleteEmployeeConfirm?.name})?
                  </p>
                  <DialogFooter>
                    <DialogClose asChild>
                      <Button variant="ghost" className="text-vault-text-secondary">Cancel</Button>
                    </DialogClose>
                    <Button 
                      onClick={() => handleDeleteEmployee(deleteEmployeeConfirm?.id || deleteEmployeeConfirm?.employee_number)}
                      className="bg-red-600 hover:bg-red-700"
                      data-testid="confirm-delete-employee-btn"
                    >
                      Delete
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </>
          )}

          {/* Guest Verification View */}
          {activeView === 'guests' && (
            <>
              {/* Header */}
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h1 className="font-outfit text-3xl font-bold text-vault-text tracking-tight">Guest Verification</h1>
                  <p className="text-vault-text-secondary font-manrope mt-1">Review and verify registered guests</p>
                </div>
                <div className="flex gap-2">
                  {registeredGuests.filter(g => !g.is_verified).length > 0 && (
                    <Button
                      onClick={handleBulkVerifyAll}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white"
                      data-testid="bulk-verify-all-btn"
                    >
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Verify All Pending ({registeredGuests.filter(g => !g.is_verified).length})
                    </Button>
                  )}
                  <Button
                    onClick={fetchRegisteredGuests}
                    className="bg-vault-surface border border-vault-border hover:bg-vault-surface-highlight text-vault-text"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Refresh
                  </Button>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                <Card className="bg-vault-surface border-vault-border">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-vault-gold/20 rounded-lg">
                        <Users className="w-5 h-5 text-vault-gold" />
                      </div>
                      <div>
                        <p className="text-vault-text-secondary text-sm">Total Guests</p>
                        <p className="text-2xl font-bold text-vault-text font-mono">{registeredGuests.length}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-vault-surface border-vault-border">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-green-500/20 rounded-lg">
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      </div>
                      <div>
                        <p className="text-vault-text-secondary text-sm">Verified</p>
                        <p className="text-2xl font-bold text-green-500 font-mono">{registeredGuests.filter(g => g.is_verified).length}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-vault-surface border-vault-border">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-amber-500/20 rounded-lg">
                        <AlertCircle className="w-5 h-5 text-amber-500" />
                      </div>
                      <div>
                        <p className="text-vault-text-secondary text-sm">Pending</p>
                        <p className="text-2xl font-bold text-amber-500 font-mono">{registeredGuests.filter(g => !g.is_verified && !g.is_blocked).length}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-vault-surface border-vault-border">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-red-500/20 rounded-lg">
                        <XCircle className="w-5 h-5 text-red-500" />
                      </div>
                      <div>
                        <p className="text-vault-text-secondary text-sm">Blocked</p>
                        <p className="text-2xl font-bold text-red-500 font-mono">{registeredGuests.filter(g => g.is_blocked).length}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Guest Table */}
              <Card className="bg-vault-surface border-vault-border">
                <CardHeader className="border-b border-vault-border">
                  <CardTitle className="font-outfit text-xl text-vault-text flex items-center gap-2">
                    <UserCheck className="w-5 h-5 text-vault-gold" />
                    Registered Guests
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <ScrollArea className="h-[400px]">
                    <Table>
                      <TableHeader>
                        <TableRow className="table-header border-vault-border hover:bg-transparent">
                          <TableHead className="text-vault-gold">Status</TableHead>
                          <TableHead className="text-vault-gold">Name</TableHead>
                          <TableHead className="text-vault-gold">Employee ID</TableHead>
                          <TableHead className="text-vault-gold">Check-ins</TableHead>
                          <TableHead className="text-vault-gold">Registered</TableHead>
                          <TableHead className="text-vault-gold">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {loadingGuests ? (
                          <TableRow>
                            <TableCell colSpan={6} className="text-center text-vault-text-secondary py-8">
                              Loading guests...
                            </TableCell>
                          </TableRow>
                        ) : registeredGuests.length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={6} className="text-center text-vault-text-secondary py-8">
                              No registered guests yet.
                            </TableCell>
                          </TableRow>
                        ) : (
                          registeredGuests.map((guest) => (
                            <TableRow key={guest.id} className={`table-row border-vault-border ${guest.is_blocked ? 'bg-red-900/30' : guest.is_flagged ? 'bg-red-900/20' : !guest.is_verified ? 'bg-amber-900/20' : ''}`}>
                              <TableCell>
                                {guest.is_blocked ? (
                                  <span className="flex items-center gap-1 text-red-500">
                                    <XCircle className="w-4 h-4" />
                                    Blocked
                                  </span>
                                ) : guest.is_flagged ? (
                                  <span className="flex items-center gap-1 text-red-400">
                                    <Flag className="w-4 h-4" />
                                    Flagged
                                  </span>
                                ) : guest.is_verified ? (
                                  <span className="flex items-center gap-1 text-green-400">
                                    <CheckCircle className="w-4 h-4" />
                                    Verified
                                  </span>
                                ) : (
                                  <span className="flex items-center gap-1 text-amber-400">
                                    <AlertCircle className="w-4 h-4" />
                                    Pending
                                  </span>
                                )}
                              </TableCell>
                              <TableCell className="text-vault-text font-medium">{guest.name}</TableCell>
                              <TableCell className="font-mono text-vault-gold">{guest.employee_number}</TableCell>
                              <TableCell className="text-vault-text">{guest.check_in_count || 0}</TableCell>
                              <TableCell className="text-vault-text-secondary text-sm">
                                {new Date(guest.created_at).toLocaleDateString()}
                              </TableCell>
                              <TableCell>
                                <div className="flex gap-1 flex-wrap">
                                  {!guest.is_verified && !guest.is_blocked && (
                                    <Button 
                                      variant="ghost" 
                                      size="sm"
                                      className="text-green-400 hover:text-green-300 hover:bg-green-500/20 h-8 px-2"
                                      onClick={() => handleVerifyGuest(guest.employee_number)}
                                      title="Verify guest"
                                    >
                                      <CheckCircle className="w-4 h-4 mr-1" />
                                      Verify
                                    </Button>
                                  )}
                                  {!guest.is_blocked ? (
                                    <Button 
                                      variant="ghost" 
                                      size="sm"
                                      className="text-red-400 hover:text-red-300 hover:bg-red-500/20 h-8 px-2"
                                      onClick={async () => {
                                        if (!confirm(`Block ${guest.name}? They won't be able to check in again.`)) return;
                                        try {
                                          await axios.post(`${API}/admin/guests/${guest.employee_number}/block`);
                                          toast.success(`${guest.name} has been blocked`);
                                          fetchRegisteredGuests();
                                        } catch (error) {
                                          toast.error("Failed to block guest");
                                        }
                                      }}
                                      title="Block guest"
                                    >
                                      <XCircle className="w-4 h-4 mr-1" />
                                      Block
                                    </Button>
                                  ) : (
                                    <Button 
                                      variant="ghost" 
                                      size="sm"
                                      className="text-blue-400 hover:text-blue-300 hover:bg-blue-500/20 h-8 px-2"
                                      onClick={async () => {
                                        try {
                                          await axios.post(`${API}/admin/guests/${guest.employee_number}/unblock`);
                                          toast.success(`${guest.name} has been unblocked`);
                                          fetchRegisteredGuests();
                                        } catch (error) {
                                          toast.error("Failed to unblock guest");
                                        }
                                      }}
                                      title="Unblock guest"
                                    >
                                      <CheckCircle className="w-4 h-4 mr-1" />
                                      Unblock
                                    </Button>
                                  )}
                                  {!guest.is_verified && (
                                    <Button 
                                      variant="ghost" 
                                      size="sm"
                                      className="text-rose-500 hover:text-rose-400 hover:bg-rose-500/20 h-8 px-2"
                                      onClick={async () => {
                                        if (!confirm(`Remove ${guest.name} from system? This cannot be undone.`)) return;
                                        try {
                                          await axios.delete(`${API}/admin/guests/${guest.employee_number}`);
                                          toast.success(`${guest.name} removed from system`);
                                          fetchRegisteredGuests();
                                        } catch (error) {
                                          toast.error("Failed to remove guest");
                                        }
                                      }}
                                      title="Remove guest"
                                    >
                                      <Trash2 className="w-4 h-4 mr-1" />
                                      Remove
                                    </Button>
                                  )}
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

          {/* Guarantee Report View */}
          {activeView === 'guarantee' && (
            <>
              {/* Header */}
              <div className="mb-6">
                <h1 className="font-outfit text-3xl font-bold text-vault-text tracking-tight">CPKC Guarantee Report</h1>
                <p className="text-vault-text-secondary font-manrope mt-1">Track CPKC room usage vs guaranteed 25 rooms - Goodwill tracking for business relations</p>
              </div>

              {/* Date Range Filter */}
              <Card className="bg-vault-surface-highlight/50 border-vault-border mb-6">
                <CardContent className="p-4">
                  <div className="flex flex-wrap items-end gap-4">
                    <div>
                      <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Start Date</label>
                      <DatePicker
                        date={guaranteeDateRange.start}
                        onDateChange={(date) => setGuaranteeDateRange({...guaranteeDateRange, start: date})}
                        placeholder="Select start"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">End Date</label>
                      <DatePicker
                        date={guaranteeDateRange.end}
                        onDateChange={(date) => setGuaranteeDateRange({...guaranteeDateRange, end: date})}
                        placeholder="Select end"
                      />
                    </div>
                    <Button
                      onClick={() => {
                        fetchGuaranteeReport(guaranteeDateRange.start, guaranteeDateRange.end);
                        fetchTurnedAwayGuests();
                      }}
                      className="bg-vault-gold hover:bg-amber-500 text-black"
                    >
                      <Search className="w-4 h-4 mr-2" />
                      Generate Report
                    </Button>
                    <Button
                      onClick={() => setShowTurnedAwayForm(true)}
                      className="bg-rose-600 hover:bg-rose-700 text-white"
                    >
                      <UserX className="w-4 h-4 mr-2" />
                      Log Turned Away Guest
                    </Button>
                    {guaranteeReport && (
                      <Button
                        onClick={downloadGuaranteeReport}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white"
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Download Excel
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Report Summary */}
              {guaranteeLoading ? (
                <div className="text-vault-text-secondary text-center py-8">Loading report...</div>
              ) : guaranteeReport ? (
                <>
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <Card className="bg-vault-surface-highlight/50 border-vault-border">
                      <CardContent className="p-4 text-center">
                        <p className="text-vault-text-secondary text-xs uppercase">Guaranteed Rooms</p>
                        <p className="text-3xl font-bold text-vault-gold">{guaranteeReport.guaranteed_rooms}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-vault-surface-highlight/50 border-vault-border">
                      <CardContent className="p-4 text-center">
                        <p className="text-vault-text-secondary text-xs uppercase">Total Days</p>
                        <p className="text-3xl font-bold text-vault-text">{guaranteeReport.total_days}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-vault-surface-highlight/50 border-vault-border">
                      <CardContent className="p-4 text-center">
                        <p className="text-vault-text-secondary text-xs uppercase">Total Unused Rooms</p>
                        <p className="text-3xl font-bold text-amber-400">{guaranteeReport.total_unused_rooms}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-emerald-900/30 border-emerald-600/50">
                      <CardContent className="p-4 text-center">
                        <p className="text-emerald-400 text-xs uppercase">Total Goodwill Given</p>
                        <p className="text-3xl font-bold text-emerald-400">${guaranteeReport.total_goodwill_amount.toFixed(2)}</p>
                        <p className="text-emerald-400/70 text-xs mt-1">(Not billed to CPKC)</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-rose-900/30 border-rose-600/50">
                      <CardContent className="p-4 text-center">
                        <p className="text-rose-400 text-xs uppercase">Guests Turned Away</p>
                        <p className="text-3xl font-bold text-rose-400">{guaranteeReport.turned_away_count || 0}</p>
                        <p className="text-rose-400/70 text-xs mt-1">(To hold for CPKC)</p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Turned Away Guests Section */}
                  {turnedAwayGuests.length > 0 && (
                    <Card className="bg-vault-surface-highlight/50 border-vault-border mb-6">
                      <CardHeader className="border-b border-vault-border pb-4">
                        <CardTitle className="font-outfit text-lg text-rose-400 flex items-center justify-between">
                          <span className="flex items-center gap-2">
                            <UserX className="w-5 h-5" />
                            Turned Away Guests Log
                          </span>
                          <span className="text-sm font-normal">
                            Lost Revenue: <span className="text-rose-400 font-bold">${turnedAwayStats.total_lost_revenue.toFixed(2)}</span>
                            <span className="text-vault-text-secondary ml-3">
                              (Single: {turnedAwayStats.single_bed_count} | Double: {turnedAwayStats.double_bed_count})
                            </span>
                          </span>
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="p-0">
                        <ScrollArea className="h-[200px]">
                          <Table>
                            <TableHeader>
                              <TableRow className="border-vault-border hover:bg-transparent">
                                <TableHead className="text-vault-gold font-bold">Date</TableHead>
                                <TableHead className="text-vault-gold font-bold">Guest</TableHead>
                                <TableHead className="text-vault-gold font-bold">Bed Type</TableHead>
                                <TableHead className="text-vault-gold font-bold">Price</TableHead>
                                <TableHead className="text-vault-gold font-bold">Reason</TableHead>
                                <TableHead className="text-vault-gold font-bold w-16"></TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {turnedAwayGuests.map((guest) => (
                                <TableRow key={guest.id} className="border-vault-border hover:bg-vault-surface">
                                  <TableCell className="font-mono text-vault-text">{guest.date}</TableCell>
                                  <TableCell className="text-vault-text">{guest.guest_name}</TableCell>
                                  <TableCell className="text-vault-text">
                                    <span className={`px-2 py-1 rounded text-xs ${guest.bed_type === 'double' ? 'bg-blue-500/20 text-blue-400' : 'bg-green-500/20 text-green-400'}`}>
                                      {guest.bed_type === 'double' ? 'Double' : 'Single'}
                                    </span>
                                  </TableCell>
                                  <TableCell className="text-rose-400 font-mono">${(guest.room_price || 0).toFixed(2)}</TableCell>
                                  <TableCell className="text-vault-text-secondary text-sm">{guest.reason}</TableCell>
                                  <TableCell>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => handleDeleteTurnedAway(guest.id)}
                                      className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                                    >
                                      <Trash2 className="w-4 h-4" />
                                    </Button>
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </ScrollArea>
                      </CardContent>
                    </Card>
                  )}

                  {/* Daily Data Table */}
                  <Card className="bg-vault-surface-highlight/50 border-vault-border">
                    <CardHeader className="border-b border-vault-border pb-4">
                      <CardTitle className="font-outfit text-lg text-vault-gold">Daily Breakdown</CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                      <ScrollArea className="h-[400px]">
                        <Table>
                          <TableHeader>
                            <TableRow className="border-vault-border hover:bg-transparent">
                              <TableHead className="text-vault-gold font-bold">Date</TableHead>
                              <TableHead className="text-vault-gold font-bold text-center">CPKC Used</TableHead>
                              <TableHead className="text-vault-gold font-bold text-center">Guaranteed</TableHead>
                              <TableHead className="text-vault-gold font-bold text-center">Unused</TableHead>
                              <TableHead className="text-vault-gold font-bold text-center">Goodwill</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {guaranteeReport.daily_data.map((day, idx) => (
                              <TableRow key={idx} className="border-vault-border hover:bg-vault-surface">
                                <TableCell className="font-mono text-vault-text">{day.date}</TableCell>
                                <TableCell className="text-center">
                                  <span className={`px-2 py-1 rounded text-sm font-medium ${
                                    day.cpkc_rooms_used >= 25 ? 'bg-green-500/20 text-green-400' :
                                    day.cpkc_rooms_used >= 20 ? 'bg-amber-500/20 text-amber-400' :
                                    'bg-red-500/20 text-red-400'
                                  }`}>
                                    {day.cpkc_rooms_used}
                                  </span>
                                </TableCell>
                                <TableCell className="text-center text-vault-text-secondary">{day.guaranteed_rooms}</TableCell>
                                <TableCell className="text-center">
                                  {day.unused_guaranteed > 0 ? (
                                    <span className="text-amber-400 font-medium">{day.unused_guaranteed}</span>
                                  ) : (
                                    <span className="text-green-400">0</span>
                                  )}
                                </TableCell>
                                <TableCell className="text-center">
                                  {day.goodwill_amount > 0 ? (
                                    <span className="text-emerald-400 font-medium">${day.goodwill_amount.toFixed(2)}</span>
                                  ) : (
                                    <span className="text-vault-text-secondary">-</span>
                                  )}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </ScrollArea>
                    </CardContent>
                  </Card>

                  {/* Note */}
                  <p className="text-vault-text-secondary text-sm mt-4 italic">
                    * Goodwill = Unused guaranteed rooms × ${guaranteeReport.nightly_rate}/night. This is revenue you could bill CPKC for but choose not to, for business relations.
                  </p>
                </>
              ) : (
                <Card className="bg-vault-surface-highlight/50 border-vault-border">
                  <CardContent className="p-8 text-center">
                    <FileBarChart className="w-12 h-12 text-vault-text-secondary mx-auto mb-4" />
                    <p className="text-vault-text-secondary">Select a date range and click "Generate Report" to view CPKC guarantee usage data.</p>
                  </CardContent>
                </Card>
              )}

              {/* Turned Away Guest Form Dialog */}
              <Dialog open={showTurnedAwayForm} onOpenChange={setShowTurnedAwayForm}>
                <DialogContent className="bg-vault-surface border-vault-border max-w-md">
                  <DialogHeader>
                    <DialogTitle className="text-vault-gold flex items-center gap-2">
                      <UserX className="w-5 h-5" />
                      Log Turned Away Guest
                    </DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <p className="text-vault-text-secondary text-sm">
                      Record when you turn away a walk-in guest to honor the CPKC room guarantee. Track lost revenue from non-CPKC rates.
                    </p>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Date</label>
                        <Input
                          type="date"
                          value={turnedAwayForm.date}
                          onChange={(e) => setTurnedAwayForm({...turnedAwayForm, date: e.target.value})}
                          className="bg-vault-surface-highlight border-vault-border text-vault-text"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Guest Name</label>
                        <Input
                          value={turnedAwayForm.guest_name}
                          onChange={(e) => setTurnedAwayForm({...turnedAwayForm, guest_name: e.target.value})}
                          placeholder="Walk-in Guest"
                          className="bg-vault-surface-highlight border-vault-border text-vault-text"
                        />
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Bed Type</label>
                        <select
                          value={turnedAwayForm.bed_type}
                          onChange={(e) => {
                            const newBedType = e.target.value;
                            const defaultPrice = newBedType === 'single' ? 85.00 : 95.00;
                            setTurnedAwayForm({...turnedAwayForm, bed_type: newBedType, room_price: defaultPrice});
                          }}
                          className="w-full h-10 px-3 rounded-md bg-vault-surface-highlight border border-vault-border text-vault-text"
                        >
                          <option value="single">Single Bed</option>
                          <option value="double">Double Bed</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Room Price ($)</label>
                        <Input
                          type="number"
                          step="0.01"
                          min="0"
                          value={turnedAwayForm.room_price}
                          onChange={(e) => setTurnedAwayForm({...turnedAwayForm, room_price: parseFloat(e.target.value) || 0})}
                          className="bg-vault-surface-highlight border-vault-border text-vault-text"
                        />
                      </div>
                    </div>
                    
                    <div>
                      <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Reason</label>
                      <Input
                        value={turnedAwayForm.reason}
                        onChange={(e) => setTurnedAwayForm({...turnedAwayForm, reason: e.target.value})}
                        placeholder="Holding rooms for CPKC"
                        className="bg-vault-surface-highlight border-vault-border text-vault-text"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Notes (Optional)</label>
                      <Input
                        value={turnedAwayForm.notes}
                        onChange={(e) => setTurnedAwayForm({...turnedAwayForm, notes: e.target.value})}
                        placeholder="Additional details..."
                        className="bg-vault-surface-highlight border-vault-border text-vault-text"
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button
                      variant="outline"
                      onClick={() => setShowTurnedAwayForm(false)}
                      className="border-vault-border text-vault-text"
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={handleLogTurnedAway}
                      className="bg-rose-600 hover:bg-rose-700 text-white"
                    >
                      Log Turned Away
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
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

                  {/* Telegram Chat ID */}
                  <div>
                    <label className="text-xs text-vault-gold uppercase tracking-wider mb-2 block font-medium">
                      Telegram Chat ID (Group)
                    </label>
                    <div className="flex gap-2">
                      <div className="relative flex-1">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-vault-text-secondary" />
                        <Input
                          type="text"
                          value={portalSettings.telegram_chat_id}
                          onChange={(e) => setPortalSettings({...portalSettings, telegram_chat_id: e.target.value})}
                          placeholder="e.g. -1001234567890"
                          className="bg-black/50 border-vault-border text-vault-text pl-10"
                          data-testid="telegram-chat-id-input"
                        />
                      </div>
                      <Button
                        onClick={async () => {
                          try {
                            // First save the settings
                            await axios.post(`${API}/admin/settings`, { 
                              telegram_chat_id: portalSettings.telegram_chat_id 
                            });
                            // Then test
                            const response = await axios.post(`${API}/admin/settings/test-telegram`);
                            if (response.data.success) {
                              toast.success(`✅ ${response.data.message}`);
                            } else {
                              toast.error(`❌ ${response.data.message}`);
                            }
                          } catch (error) {
                            toast.error("Failed to test Telegram");
                          }
                        }}
                        className="bg-blue-600 hover:bg-blue-700 text-white whitespace-nowrap"
                        data-testid="test-telegram-btn"
                      >
                        Test Telegram
                      </Button>
                    </div>
                    <p className="text-vault-text-secondary text-xs mt-1">
                      All check-in/check-out alerts will be sent to this Telegram group.
                      <br />
                      <span className="text-vault-gold">Correct group ID: -1003798795772</span>
                    </p>
                  </div>

                  {/* Public API Section */}
                  <div className="pt-4 border-t border-vault-border">
                    <h4 className="text-vault-gold font-medium mb-4 flex items-center gap-2">
                      <Shield className="w-4 h-4" />
                      Public API Access
                    </h4>
                    
                    {/* API Key */}
                    <div className="mb-4">
                      <label className="text-xs text-vault-gold uppercase tracking-wider mb-2 block font-medium">
                        API Key
                      </label>
                      <div className="flex gap-2">
                        <div className="relative flex-1">
                          <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-vault-text-secondary" />
                          <Input
                            type="text"
                            value={portalSettings.public_api_key}
                            onChange={(e) => setPortalSettings({...portalSettings, public_api_key: e.target.value})}
                            placeholder="Enter API key for external access"
                            className="bg-black/50 border-vault-border text-vault-text pl-10 font-mono text-sm"
                            data-testid="public-api-key-input"
                          />
                        </div>
                        <Button
                          type="button"
                          onClick={() => {
                            const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
                            let key = 'hinn_';
                            for (let i = 0; i < 32; i++) {
                              key += chars.charAt(Math.floor(Math.random() * chars.length));
                            }
                            setPortalSettings({...portalSettings, public_api_key: key});
                            toast.success("New secure API key generated! Click Save Settings to apply.");
                          }}
                          className="bg-vault-gold/20 text-vault-gold hover:bg-vault-gold/30 border border-vault-gold/50"
                          data-testid="generate-api-key-btn"
                        >
                          <RefreshCw className="w-4 h-4 mr-1" />
                          Generate
                        </Button>
                      </div>
                      <p className="text-vault-text-secondary text-xs mt-1">
                        Share this key with authorized systems. Click Generate for a secure random key.
                      </p>
                    </div>

                    {/* Nightly Rate */}
                    <div className="mb-4">
                      <label className="text-xs text-vault-gold uppercase tracking-wider mb-2 block font-medium">
                        Nightly Rate ($)
                      </label>
                      <Input
                        type="number"
                        value={portalSettings.nightly_rate}
                        onChange={(e) => setPortalSettings({...portalSettings, nightly_rate: parseFloat(e.target.value) || 0})}
                        placeholder="75.00"
                        className="bg-black/50 border-vault-border text-vault-text w-32"
                        data-testid="nightly-rate-input"
                      />
                      <p className="text-vault-text-secondary text-xs mt-1">
                        Rate per night used in billing calculations.
                      </p>
                    </div>

                    {/* API Documentation Panel */}
                    {portalSettings.public_api_key && (
                      <div className="bg-black/70 rounded-lg p-4 mt-4 border border-vault-border">
                        <div className="flex items-center justify-between mb-4">
                          <p className="text-vault-gold text-sm font-medium flex items-center gap-2">
                            <Link className="w-4 h-4" />
                            API Documentation
                          </p>
                          <Button
                            size="sm"
                            onClick={() => {
                              const baseUrl = window.location.origin;
                              const docText = `HODLER INN API DOCUMENTATION

BASE URL: ${baseUrl}

API KEY: ${portalSettings.public_api_key}

ENDPOINTS:

1. Sign-in Sheets
   ${baseUrl}/api/public/signin-sheets?api_key=${portalSettings.public_api_key}

2. Billing Report
   ${baseUrl}/api/public/billing-report?api_key=${portalSettings.public_api_key}

OPTIONAL PARAMETERS:
- format=csv (default: json)
- start_date=YYYY-MM-DD
- end_date=YYYY-MM-DD

EXAMPLES:

All records (JSON):
${baseUrl}/api/public/signin-sheets?api_key=${portalSettings.public_api_key}

Billing as CSV:
${baseUrl}/api/public/billing-report?api_key=${portalSettings.public_api_key}&format=csv

Date filtered:
${baseUrl}/api/public/signin-sheets?api_key=${portalSettings.public_api_key}&start_date=2026-03-01&end_date=2026-03-31`;
                              navigator.clipboard.writeText(docText);
                              toast.success("Full API documentation copied to clipboard!");
                            }}
                            className="bg-vault-gold/20 text-vault-gold hover:bg-vault-gold/30 text-xs"
                            data-testid="copy-all-docs-btn"
                          >
                            <Copy className="w-3 h-3 mr-1" />
                            Copy All
                          </Button>
                        </div>

                        {/* Base URL */}
                        <div className="mb-3">
                          <label className="text-vault-text-secondary text-xs mb-1 block">Base URL</label>
                          <div className="flex items-center gap-2 bg-black/50 rounded px-3 py-2">
                            <code className="text-green-400 text-sm flex-1 break-all">{window.location.origin}</code>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                navigator.clipboard.writeText(window.location.origin);
                                toast.success("Base URL copied!");
                              }}
                              className="h-6 w-6 p-0 text-vault-text-secondary hover:text-vault-gold"
                            >
                              <Copy className="w-3 h-3" />
                            </Button>
                          </div>
                        </div>

                        {/* API Key Display */}
                        <div className="mb-3">
                          <label className="text-vault-text-secondary text-xs mb-1 block">Your API Key</label>
                          <div className="flex items-center gap-2 bg-black/50 rounded px-3 py-2">
                            <code className="text-amber-400 text-sm flex-1 font-mono">{portalSettings.public_api_key}</code>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                navigator.clipboard.writeText(portalSettings.public_api_key);
                                toast.success("API Key copied!");
                              }}
                              className="h-6 w-6 p-0 text-vault-text-secondary hover:text-vault-gold"
                            >
                              <Copy className="w-3 h-3" />
                            </Button>
                          </div>
                        </div>

                        {/* Endpoints */}
                        <div className="space-y-3">
                          <label className="text-vault-text-secondary text-xs block">Endpoints (Click to copy full URL)</label>
                          
                          {/* Sign-in Sheets Endpoint */}
                          <div 
                            className="bg-black/50 rounded px-3 py-2 cursor-pointer hover:bg-black/70 transition-colors group"
                            onClick={() => {
                              const url = `${window.location.origin}/api/public/signin-sheets?api_key=${portalSettings.public_api_key}`;
                              navigator.clipboard.writeText(url);
                              toast.success("Sign-in Sheets URL copied!");
                            }}
                          >
                            <div className="flex items-center justify-between">
                              <div>
                                <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded mr-2">GET</span>
                                <span className="text-vault-text text-sm">Sign-in Sheets</span>
                              </div>
                              <Copy className="w-3 h-3 text-vault-text-secondary group-hover:text-vault-gold" />
                            </div>
                            <code className="text-vault-text-secondary text-xs mt-1 block break-all">
                              /api/public/signin-sheets?api_key=...
                            </code>
                          </div>

                          {/* Billing Report Endpoint */}
                          <div 
                            className="bg-black/50 rounded px-3 py-2 cursor-pointer hover:bg-black/70 transition-colors group"
                            onClick={() => {
                              const url = `${window.location.origin}/api/public/billing-report?api_key=${portalSettings.public_api_key}`;
                              navigator.clipboard.writeText(url);
                              toast.success("Billing Report URL copied!");
                            }}
                          >
                            <div className="flex items-center justify-between">
                              <div>
                                <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded mr-2">GET</span>
                                <span className="text-vault-text text-sm">Billing Report</span>
                              </div>
                              <Copy className="w-3 h-3 text-vault-text-secondary group-hover:text-vault-gold" />
                            </div>
                            <code className="text-vault-text-secondary text-xs mt-1 block break-all">
                              /api/public/billing-report?api_key=...
                            </code>
                          </div>
                        </div>

                        {/* Parameters Table */}
                        <div className="mt-4 pt-3 border-t border-vault-border">
                          <label className="text-vault-text-secondary text-xs mb-2 block">Optional Parameters</label>
                          <div className="grid grid-cols-3 gap-2 text-xs">
                            <div className="bg-black/50 rounded p-2">
                              <code className="text-blue-400">format</code>
                              <p className="text-vault-text-secondary mt-1">json / csv</p>
                            </div>
                            <div className="bg-black/50 rounded p-2">
                              <code className="text-blue-400">start_date</code>
                              <p className="text-vault-text-secondary mt-1">YYYY-MM-DD</p>
                            </div>
                            <div className="bg-black/50 rounded p-2">
                              <code className="text-blue-400">end_date</code>
                              <p className="text-vault-text-secondary mt-1">YYYY-MM-DD</p>
                            </div>
                          </div>
                        </div>

                        {/* Quick Links */}
                        <div className="mt-4 pt-3 border-t border-vault-border">
                          <label className="text-vault-text-secondary text-xs mb-2 block">Quick Test Links</label>
                          <div className="flex flex-wrap gap-2">
                            <a
                              href={`${window.location.origin}/api/public/signin-sheets?api_key=${portalSettings.public_api_key}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs bg-vault-gold/20 text-vault-gold px-3 py-1.5 rounded hover:bg-vault-gold/30 transition-colors"
                            >
                              Open Sign-in (JSON)
                            </a>
                            <a
                              href={`${window.location.origin}/api/public/signin-sheets?api_key=${portalSettings.public_api_key}&format=csv`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs bg-vault-gold/20 text-vault-gold px-3 py-1.5 rounded hover:bg-vault-gold/30 transition-colors"
                            >
                              Download Sign-in (CSV)
                            </a>
                            <a
                              href={`${window.location.origin}/api/public/billing-report?api_key=${portalSettings.public_api_key}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs bg-vault-gold/20 text-vault-gold px-3 py-1.5 rounded hover:bg-vault-gold/30 transition-colors"
                            >
                              Open Billing (JSON)
                            </a>
                            <a
                              href={`${window.location.origin}/api/public/billing-report?api_key=${portalSettings.public_api_key}&format=csv`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs bg-vault-gold/20 text-vault-gold px-3 py-1.5 rounded hover:bg-vault-gold/30 transition-colors"
                            >
                              Download Billing (CSV)
                            </a>
                          </div>
                        </div>
                      </div>
                    )}
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

              {/* Sync Controls Card */}
              <Card className="bg-vault-surface border-vault-border max-w-2xl mt-6" data-testid="sync-controls-card">
                <CardHeader className="border-b border-vault-border">
                  <CardTitle className="font-outfit text-xl text-vault-text flex items-center gap-2">
                    <Globe className="w-5 h-5 text-vault-gold" />
                    API Global Sync
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6 space-y-4">
                  {/* Auto-Sync Toggle */}
                  <div className="bg-black/50 border border-vault-border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-vault-text font-medium">Auto-Sync (Daily at 3 PM)</h4>
                        <p className="text-vault-text-secondary text-sm">
                          Automatically verify previous day's records every day at 3 PM
                        </p>
                      </div>
                      <button
                        onClick={async () => {
                          const newValue = !portalSettings.auto_sync_enabled;
                          setPortalSettings({...portalSettings, auto_sync_enabled: newValue});
                          try {
                            await axios.post(`${API}/admin/settings`, { auto_sync_enabled: newValue });
                            toast.success(newValue ? "Auto-sync enabled! Will run daily at 3 PM" : "Auto-sync disabled");
                          } catch (error) {
                            toast.error("Failed to update auto-sync setting");
                            setPortalSettings({...portalSettings, auto_sync_enabled: !newValue});
                          }
                        }}
                        disabled={!portalSettings.api_global_password_set}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          portalSettings.auto_sync_enabled ? 'bg-emerald-600' : 'bg-gray-600'
                        } ${!portalSettings.api_global_password_set ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                        data-testid="auto-sync-toggle"
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            portalSettings.auto_sync_enabled ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>
                    {syncStatus.next_scheduled_run && portalSettings.auto_sync_enabled && (
                      <p className="text-emerald-400 text-sm mt-2">
                        Next scheduled sync: {new Date(syncStatus.next_scheduled_run).toLocaleString()}
                      </p>
                    )}
                    
                    {/* Auto-Sync Start Date */}
                    {portalSettings.auto_sync_enabled && (
                      <div className="mt-3 flex items-center gap-3 bg-black/30 p-3 rounded-lg border border-vault-border">
                        <label className="text-vault-text-secondary text-sm whitespace-nowrap">Start Date:</label>
                        <DatePicker
                          date={portalSettings.auto_sync_start_date}
                          onDateChange={(date) => setPortalSettings({...portalSettings, auto_sync_start_date: date})}
                          placeholder="Select start date"
                        />
                        <Button
                          onClick={async () => {
                            try {
                              await axios.post(`${API}/admin/settings`, { 
                                auto_sync_enabled: true,
                                auto_sync_start_date: portalSettings.auto_sync_start_date 
                              });
                              toast.success(`Auto-sync will start from ${portalSettings.auto_sync_start_date || 'today'}`);
                            } catch (error) {
                              toast.error("Failed to update start date");
                            }
                          }}
                          className="bg-emerald-600 hover:bg-emerald-700 text-white text-sm h-9 px-3"
                          data-testid="save-auto-sync-date-btn"
                        >
                          Save Start Date
                        </Button>
                        <span className="text-vault-text-secondary text-xs">
                          {portalSettings.auto_sync_start_date 
                            ? `Sync will skip dates before ${portalSettings.auto_sync_start_date}` 
                            : "Leave empty to start immediately"}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Manual Sync Buttons */}
                  <div className="space-y-3">
                    {/* Date Picker for Manual Sync */}
                    <div className="flex items-center gap-3 bg-black/30 p-3 rounded-lg border border-vault-border">
                      <label className="text-vault-text-secondary text-sm whitespace-nowrap">Sync Date:</label>
                      <DatePicker
                        date={syncTargetDate}
                        onDateChange={setSyncTargetDate}
                        placeholder="Select sync date"
                      />
                      <span className="text-vault-text-secondary text-xs">
                        {syncTargetDate ? `Selected: ${syncTargetDate}` : "Leave empty for yesterday/today"}
                      </span>
                    </div>
                    
                    <div className="flex flex-wrap gap-3">
                      <Button
                        onClick={handleTestConnection}
                        disabled={runningSyncTest || !portalSettings.api_global_password_set}
                        className="bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-2"
                        data-testid="test-connection-btn"
                      >
                        <Key className="w-4 h-4" />
                        {runningSyncTest ? "Testing..." : "Test Connection"}
                      </Button>
                      <Button
                        onClick={handleRunSync}
                        disabled={syncStatus.running || !portalSettings.api_global_password_set}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white flex items-center gap-2"
                        data-testid="run-sync-btn"
                      >
                        <Globe className="w-4 h-4" />
                        {syncStatus.running ? "Syncing..." : "Run Sync Now"}
                      </Button>
                    </div>
                  </div>
                  
                  {!portalSettings.api_global_password_set && (
                    <p className="text-amber-400 text-sm">
                      Please save your portal credentials first before running sync.
                    </p>
                  )}
                  
                  {syncStatus.running && (
                    <div className="bg-black/50 border border-vault-border rounded-lg p-4">
                      <p className="text-vault-gold text-sm flex items-center gap-2">
                        <span className="animate-spin">⚡</span>
                        {syncStatus.progress || "Sync in progress..."}
                      </p>
                    </div>
                  )}
                  
                  {syncStatus.last_results && !syncStatus.running && (
                    <div className="bg-black/50 border border-vault-border rounded-lg p-4">
                      <h4 className="text-vault-gold font-bold mb-2">Last Sync Results:</h4>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <p className="text-green-400">Verified: {syncStatus.last_results.verified?.length || 0}</p>
                        <p className="text-amber-400">No Bill: {syncStatus.last_results.no_bill?.length || 0}</p>
                        <p className="text-blue-400">Missing: {syncStatus.last_results.missing_in_hodler?.length || 0}</p>
                        <p className="text-red-400">Errors: {syncStatus.last_results.errors?.length || 0}</p>
                      </div>
                      {syncStatus.last_run && (
                        <p className="text-vault-text-secondary text-xs mt-2">
                          Last run: {new Date(syncStatus.last_run).toLocaleString()}
                        </p>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Voice Control */}
              <Card className="bg-vault-surface border-vault-border max-w-2xl mt-6" data-testid="voice-control-card">
                <CardHeader className="border-b border-vault-border">
                  <CardTitle className="font-outfit text-xl text-vault-text flex items-center gap-2">
                    {portalSettings.voice_enabled ? (
                      <Volume2 className="w-5 h-5 text-vault-gold" />
                    ) : (
                      <VolumeX className="w-5 h-5 text-vault-text-secondary" />
                    )}
                    Voice Messages
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6 space-y-4">
                  <p className="text-vault-text-secondary text-sm">
                    Control voice announcements on the guest kiosk after check-in and check-out.
                  </p>
                  
                  {/* Voice Enable/Disable Toggle */}
                  <div className="bg-black/50 border border-vault-border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-vault-text font-medium">Voice Announcements</h4>
                        <p className="text-vault-text-secondary text-sm">
                          {portalSettings.voice_enabled 
                            ? "Voice messages will play after check-in and check-out" 
                            : "Voice messages are muted"}
                        </p>
                      </div>
                      <button
                        onClick={async () => {
                          const newValue = !portalSettings.voice_enabled;
                          setPortalSettings({...portalSettings, voice_enabled: newValue});
                          try {
                            await axios.post(`${API}/admin/settings`, { voice_enabled: newValue });
                            toast.success(newValue ? "Voice enabled" : "Voice muted");
                          } catch (error) {
                            toast.error("Failed to update voice setting");
                            setPortalSettings({...portalSettings, voice_enabled: !newValue});
                          }
                        }}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          portalSettings.voice_enabled ? 'bg-emerald-600' : 'bg-gray-600'
                        } cursor-pointer`}
                        data-testid="voice-toggle"
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            portalSettings.voice_enabled ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>
                  </div>
                  
                  {/* Volume Slider */}
                  {portalSettings.voice_enabled && (
                    <div className="bg-black/50 border border-vault-border rounded-lg p-4">
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <h4 className="text-vault-text font-medium">Volume</h4>
                          <span className="text-vault-gold font-mono text-sm">
                            {Math.round(portalSettings.voice_volume * 100)}%
                          </span>
                        </div>
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={portalSettings.voice_volume * 100}
                          onChange={async (e) => {
                            const newVolume = parseInt(e.target.value) / 100;
                            setPortalSettings({...portalSettings, voice_volume: newVolume});
                          }}
                          onMouseUp={async (e) => {
                            const newVolume = parseInt(e.target.value) / 100;
                            try {
                              await axios.post(`${API}/admin/settings`, { voice_volume: newVolume });
                              toast.success(`Volume set to ${Math.round(newVolume * 100)}%`);
                            } catch (error) {
                              toast.error("Failed to update volume");
                            }
                          }}
                          onTouchEnd={async (e) => {
                            const newVolume = portalSettings.voice_volume;
                            try {
                              await axios.post(`${API}/admin/settings`, { voice_volume: newVolume });
                              toast.success(`Volume set to ${Math.round(newVolume * 100)}%`);
                            } catch (error) {
                              toast.error("Failed to update volume");
                            }
                          }}
                          className="w-full h-2 bg-vault-border rounded-lg appearance-none cursor-pointer accent-vault-gold"
                          data-testid="voice-volume-slider"
                        />
                        <div className="flex justify-between text-vault-text-secondary text-xs">
                          <span>Mute</span>
                          <span>Max</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Voice Speed Control */}
                  {portalSettings.voice_enabled && (
                    <div className="bg-black/50 border border-vault-border rounded-lg p-4">
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <h4 className="text-vault-text font-medium">Voice Speed</h4>
                          <span className="text-vault-gold font-mono text-sm">
                            {portalSettings.voice_speed <= 0.7 ? 'Slow' : portalSettings.voice_speed >= 1.0 ? 'Fast' : 'Normal'} ({portalSettings.voice_speed})
                          </span>
                        </div>
                        <input
                          type="range"
                          min="50"
                          max="120"
                          step="5"
                          value={portalSettings.voice_speed * 100}
                          onChange={async (e) => {
                            const newSpeed = parseInt(e.target.value) / 100;
                            setPortalSettings({...portalSettings, voice_speed: newSpeed});
                          }}
                          onMouseUp={async (e) => {
                            const newSpeed = parseInt(e.target.value) / 100;
                            try {
                              await axios.post(`${API}/admin/settings`, { voice_speed: newSpeed });
                              toast.success(`Voice speed set to ${newSpeed}`);
                            } catch (error) {
                              toast.error("Failed to update voice speed");
                            }
                          }}
                          onTouchEnd={async (e) => {
                            const newSpeed = portalSettings.voice_speed;
                            try {
                              await axios.post(`${API}/admin/settings`, { voice_speed: newSpeed });
                              toast.success(`Voice speed set to ${newSpeed}`);
                            } catch (error) {
                              toast.error("Failed to update voice speed");
                            }
                          }}
                          className="w-full h-2 bg-vault-border rounded-lg appearance-none cursor-pointer accent-vault-gold"
                          data-testid="voice-speed-slider"
                        />
                        <div className="flex justify-between text-vault-text-secondary text-xs">
                          <span>Slow (0.5)</span>
                          <span>Normal (0.85)</span>
                          <span>Fast (1.2)</span>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Test Voice Button */}
                  <Button
                    onClick={() => {
                      if ('speechSynthesis' in window) {
                        window.speechSynthesis.cancel();
                        const utterance = new SpeechSynthesisUtterance("Good afternoon! Welcome to Hodler Inn. Please enter room number, time, sign your name, and click Complete Check-In.");
                        utterance.volume = portalSettings.voice_volume;
                        utterance.rate = portalSettings.voice_speed;
                        window.speechSynthesis.speak(utterance);
                        toast.success("Playing test message...");
                      } else {
                        toast.error("Voice not supported in this browser");
                      }
                    }}
                    disabled={!portalSettings.voice_enabled}
                    className="bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-2"
                    data-testid="test-voice-btn"
                  >
                    <Volume2 className="w-4 h-4" />
                    Test Voice
                  </Button>
                </CardContent>
              </Card>

              {/* Email Reports Section */}
              <Card className="bg-vault-surface-highlight/50 border-vault-border max-w-2xl mt-6">
                <CardContent className="p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-outfit text-lg font-bold text-vault-gold flex items-center gap-2">
                      <Mail className="w-5 h-5" />
                      Daily Email Reports
                    </h3>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <span className="text-vault-text-secondary text-sm">
                        {portalSettings.email_reports_enabled ? "Enabled" : "Disabled"}
                      </span>
                      <input
                        type="checkbox"
                        checked={portalSettings.email_reports_enabled}
                        onChange={async (e) => {
                          const enabled = e.target.checked;
                          setPortalSettings({...portalSettings, email_reports_enabled: enabled});
                          try {
                            await axios.post(`${API}/admin/settings`, { email_reports_enabled: enabled });
                            toast.success(enabled ? "Email reports enabled" : "Email reports disabled");
                          } catch (error) {
                            toast.error("Failed to update setting");
                          }
                        }}
                        className="w-5 h-5 accent-vault-gold"
                        data-testid="email-reports-toggle"
                      />
                    </label>
                  </div>
                  <p className="text-vault-text-secondary text-sm">
                    Automatically email sign-in sheets and billing records as PDF attachments daily.
                  </p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* SMTP Host */}
                    <div>
                      <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">SMTP Host</label>
                      <Input
                        value={portalSettings.email_smtp_host}
                        onChange={(e) => setPortalSettings({...portalSettings, email_smtp_host: e.target.value})}
                        placeholder="smtp.zoho.com"
                        className="bg-black/50 border-vault-border text-vault-text"
                        data-testid="email-smtp-host"
                      />
                    </div>

                    {/* SMTP Port */}
                    <div>
                      <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">SMTP Port</label>
                      <Input
                        type="number"
                        value={portalSettings.email_smtp_port}
                        onChange={(e) => setPortalSettings({...portalSettings, email_smtp_port: parseInt(e.target.value) || 587})}
                        placeholder="587"
                        className="bg-black/50 border-vault-border text-vault-text"
                        data-testid="email-smtp-port"
                      />
                    </div>
                  </div>

                  {/* Sender Email */}
                  <div>
                    <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Sender Email (Your Zoho Email)</label>
                    <Input
                      value={portalSettings.email_sender}
                      onChange={(e) => setPortalSettings({...portalSettings, email_sender: e.target.value})}
                      placeholder="your-email@yourdomain.com"
                      className="bg-black/50 border-vault-border text-vault-text"
                      data-testid="email-sender"
                    />
                  </div>

                  {/* Email Password */}
                  <div>
                    <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">
                      Email Password {portalSettings.email_password_set && <span className="text-emerald-400">(Set ✓)</span>}
                    </label>
                    <Input
                      type="password"
                      value={portalSettings.email_password}
                      onChange={(e) => setPortalSettings({...portalSettings, email_password: e.target.value})}
                      placeholder={portalSettings.email_password_set ? "••••••••" : "Enter password or app password"}
                      className="bg-black/50 border-vault-border text-vault-text"
                      data-testid="email-password"
                    />
                    <p className="text-vault-text-secondary text-xs mt-1">
                      Use an App Password if you have 2FA enabled on Zoho
                    </p>
                  </div>

                  {/* Recipient Email */}
                  <div>
                    <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Send Reports To</label>
                    <Input
                      value={portalSettings.email_recipient}
                      onChange={(e) => setPortalSettings({...portalSettings, email_recipient: e.target.value})}
                      placeholder="signinsheets@hodlerinn.com"
                      className="bg-black/50 border-vault-border text-vault-text"
                      data-testid="email-recipient"
                    />
                  </div>

                  {/* Report Time */}
                  <div>
                    <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Send Report At (Your Local Time)</label>
                    <Input
                      type="time"
                      value={portalSettings.email_report_time}
                      onChange={(e) => setPortalSettings({...portalSettings, email_report_time: e.target.value})}
                      className="bg-black/50 border-vault-border text-vault-text w-40"
                      data-testid="email-report-time"
                    />
                  </div>

                  {/* Save & Test Buttons */}
                  <div className="flex gap-3 pt-2">
                    <Button
                      onClick={async () => {
                        setSavingSettings(true);
                        try {
                          await axios.post(`${API}/admin/settings`, {
                            email_reports_enabled: portalSettings.email_reports_enabled,
                            email_smtp_host: portalSettings.email_smtp_host,
                            email_smtp_port: portalSettings.email_smtp_port,
                            email_sender: portalSettings.email_sender,
                            email_password: portalSettings.email_password || null,
                            email_recipient: portalSettings.email_recipient,
                            email_report_time: portalSettings.email_report_time
                          });
                          toast.success("Email settings saved!");
                          fetchSettings();
                        } catch (error) {
                          toast.error("Failed to save settings");
                        } finally {
                          setSavingSettings(false);
                        }
                      }}
                      disabled={savingSettings}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white"
                      data-testid="save-email-settings-btn"
                    >
                      {savingSettings ? "Saving..." : "Save Email Settings"}
                    </Button>
                    <Button
                      onClick={async () => {
                        setTestingEmail(true);
                        try {
                          const res = await axios.post(`${API}/admin/settings/test-email`);
                          if (res.data.success) {
                            toast.success(res.data.message);
                          } else {
                            toast.error(res.data.message);
                          }
                        } catch (error) {
                          toast.error(error.response?.data?.detail || "Failed to send test email");
                        } finally {
                          setTestingEmail(false);
                        }
                      }}
                      disabled={testingEmail || !portalSettings.email_sender}
                      className="bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-2"
                      data-testid="test-email-btn"
                    >
                      <Mail className="w-4 h-4" />
                      {testingEmail ? "Sending..." : "Send Test Email"}
                    </Button>
                  </div>
                  
                  {/* CPKC Email Notification Test Buttons */}
                  <div className="border-t border-vault-border pt-4 mt-4">
                    <h4 className="text-sm font-semibold text-vault-gold mb-3">Test CPKC Notifications</h4>
                    <p className="text-vault-text-secondary text-xs mb-3">
                      Test the automated email notifications sent to CPKC (crewtravel@cpkcr.com, crewmanagers@cpkcr.com)
                    </p>
                    <div className="flex flex-wrap gap-3">
                      <Button
                        onClick={async () => {
                          try {
                            const res = await axios.post(`${API}/admin/settings/test-room-available`);
                            if (res.data.success) {
                              toast.success(res.data.message);
                            } else {
                              toast.error(res.data.message);
                            }
                          } catch (error) {
                            toast.error("Failed to send test notification");
                          }
                        }}
                        disabled={!portalSettings.email_sender}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white text-sm"
                        data-testid="test-room-available-btn"
                      >
                        Test Room Available Alert
                      </Button>
                      <Button
                        onClick={async () => {
                          try {
                            const res = await axios.post(`${API}/admin/settings/test-heads-up`);
                            if (res.data.success) {
                              toast.success(res.data.message);
                            } else {
                              toast.error(res.data.message);
                            }
                          } catch (error) {
                            toast.error("Failed to send test notification");
                          }
                        }}
                        disabled={!portalSettings.email_sender}
                        className="bg-amber-600 hover:bg-amber-700 text-white text-sm"
                        data-testid="test-heads-up-btn"
                      >
                        Test Heads-Up Notice
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Zoho Drive Section */}
              <Card className="bg-vault-surface-highlight/50 border-vault-border max-w-2xl mt-6">
                <CardContent className="p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-outfit text-lg font-bold text-vault-gold flex items-center gap-2">
                      <Cloud className="w-5 h-5" />
                      Zoho WorkDrive Backup
                    </h3>
                    <span className="text-emerald-400 text-sm flex items-center gap-1">
                      <CheckCircle className="w-4 h-4" />
                      Connected
                    </span>
                  </div>
                  <p className="text-vault-text-secondary text-sm">
                    Upload sign-in sheets with signatures to your Zoho WorkDrive. Select a date to upload missed reports.
                  </p>
                  
                  <div className="flex flex-wrap items-end gap-3">
                    <div>
                      <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Report Date</label>
                      <Input
                        type="date"
                        value={zohoUploadDate}
                        onChange={(e) => setZohoUploadDate(e.target.value)}
                        className="bg-vault-surface border-vault-border text-vault-text w-40"
                      />
                    </div>
                    <Button
                      onClick={async () => {
                        setTestingZoho(true);
                        try {
                          const res = await axios.post(`${API}/admin/settings/test-zoho`);
                          if (res.data.success) {
                            toast.success(res.data.message);
                          } else {
                            toast.error(res.data.message);
                          }
                        } catch (error) {
                          toast.error("Failed to test Zoho connection");
                        } finally {
                          setTestingZoho(false);
                        }
                      }}
                      disabled={testingZoho}
                      className="bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-2"
                      data-testid="test-zoho-btn"
                    >
                      <Cloud className="w-4 h-4" />
                      {testingZoho ? "Testing..." : "Test Connection"}
                    </Button>
                    <Button
                      onClick={async () => {
                        setUploadingZoho(true);
                        try {
                          const res = await axios.post(`${API}/admin/upload-to-zoho?target_date=${zohoUploadDate}`);
                          toast.success(`Reports for ${zohoUploadDate} uploaded to Zoho Drive!`);
                          console.log(res.data);
                        } catch (error) {
                          toast.error("Failed to upload to Zoho Drive");
                        } finally {
                          setUploadingZoho(false);
                        }
                      }}
                      disabled={uploadingZoho}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white flex items-center gap-2"
                      data-testid="upload-zoho-btn"
                    >
                      <Upload className="w-4 h-4" />
                      {uploadingZoho ? "Uploading..." : "Upload Report"}
                    </Button>
                  </div>
                  <p className="text-vault-text-secondary text-xs">
                    Reports include signature images and check-in/out times.
                  </p>
                </CardContent>
              </Card>

              {/* Info Box */}
              <Card className="bg-vault-surface-highlight/50 border-vault-border max-w-2xl mt-6">
                <CardContent className="p-6">
                  <h3 className="font-outfit text-lg font-bold text-vault-gold mb-3">How AI Verification Works</h3>
                  <ol className="text-vault-text-secondary text-sm space-y-2 list-decimal list-inside">
                    <li>AI agent logs into API Global portal with your credentials</li>
                    <li>Loads sign-in sheets for the previous day</li>
                    <li>Matches names with your Hodler Inn records</li>
                    <li>Auto-fills Employee ID and Room Number for each match</li>
                    <li>Marks "No Bill" for entries not in your records</li>
                    <li>Sends Telegram notification with sync results</li>
                  </ol>
                  <div className="bg-emerald-900/30 border border-emerald-600/30 rounded-lg p-3 mt-4">
                    <p className="text-emerald-400 text-sm">
                      <strong>✓ Auto-Sync Available:</strong> Enable the toggle above to automatically run verification daily at 3 PM
                    </p>
                  </div>
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

      {/* Block Room Dialog (Other Guest) */}
      {showBlockRoomDialog && (
        <Dialog open={showBlockRoomDialog} onOpenChange={() => setShowBlockRoomDialog(false)}>
          <DialogContent className="bg-vault-surface border-vault-border">
            <DialogHeader>
              <DialogTitle className="font-outfit text-vault-text flex items-center gap-2">
                <Users className="w-5 h-5 text-amber-400" />
                Block Room for Other Guest
              </DialogTitle>
            </DialogHeader>
            <p className="text-vault-text-secondary text-sm mb-4">
              Block a room for a non-railroad guest. This room will count toward occupancy but will NOT be billed to the railroad.
            </p>
            <div className="space-y-4">
              <div>
                <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Room Number *</label>
                <Select 
                  value={blockRoomForm.room_number} 
                  onValueChange={(val) => setBlockRoomForm({...blockRoomForm, room_number: val})}
                >
                  <SelectTrigger className="bg-black/50 border-vault-border text-vault-text">
                    <SelectValue placeholder="Select available room" />
                  </SelectTrigger>
                  <SelectContent className="bg-vault-surface border-vault-border">
                    {rooms
                      .filter(r => r.status === 'available' && !blockedRooms.some(b => b.room_number === r.room_number))
                      .map(room => (
                        <SelectItem key={room.id} value={room.room_number} className="text-vault-text">
                          Room {room.room_number} ({room.room_type})
                        </SelectItem>
                      ))
                    }
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Guest Name (Optional)</label>
                <Input
                  value={blockRoomForm.guest_name}
                  onChange={(e) => setBlockRoomForm({...blockRoomForm, guest_name: e.target.value})}
                  placeholder="e.g. Walk-in Guest, John Doe"
                  className="bg-black/50 border-vault-border text-vault-text"
                />
              </div>
              <div>
                <label className="text-xs text-vault-gold uppercase tracking-wider mb-1 block">Notes (Optional)</label>
                <Input
                  value={blockRoomForm.notes}
                  onChange={(e) => setBlockRoomForm({...blockRoomForm, notes: e.target.value})}
                  placeholder="e.g. Paid cash, 2 nights"
                  className="bg-black/50 border-vault-border text-vault-text"
                />
              </div>
            </div>
            <DialogFooter className="mt-4">
              <Button variant="ghost" onClick={() => setShowBlockRoomDialog(false)} className="text-vault-text-secondary">
                Cancel
              </Button>
              <Button 
                onClick={handleBlockRoom}
                className="bg-amber-600 hover:bg-amber-700 text-white"
                data-testid="confirm-block-room-btn"
              >
                Block Room
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
