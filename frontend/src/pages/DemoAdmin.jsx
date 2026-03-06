import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { 
  Home, 
  Users, 
  DoorOpen, 
  RefreshCw,
  Settings,
  Bed,
  LayoutDashboard,
  FileSpreadsheet,
  UserCheck,
  TrendingUp
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api/demo`;

export default function DemoAdmin() {
  const [stats, setStats] = useState({ total_rooms: 28, occupied: 0, available: 28, occupancy_rate: 0 });
  const [guests, setGuests] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("dashboard");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, guestsRes, employeesRes, settingsRes] = await Promise.all([
        axios.get(`${API}/stats`),
        axios.get(`${API}/guests`),
        axios.get(`${API}/employees`),
        axios.get(`${API}/settings`)
      ]);
      setStats(statsRes.data);
      setGuests(guestsRes.data);
      setEmployees(employeesRes.data);
      setSettings(settingsRes.data);
    } catch (error) {
      console.error("Failed to fetch demo data");
    }
  };

  const initializeDemo = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/init`);
      toast.success("Demo data initialized!");
      fetchData();
    } catch (error) {
      toast.error("Failed to initialize demo");
    }
    setLoading(false);
  };

  const activeGuests = guests.filter(g => !g.is_checked_out);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Sidebar */}
      <div className="fixed left-0 top-0 h-full w-64 bg-black/60 border-r border-amber-500/20 p-4">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 bg-gradient-to-br from-amber-400 to-amber-600 rounded-full flex items-center justify-center">
            <Home className="w-5 h-5 text-black" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">Hodler Inn</h1>
            <p className="text-amber-400 text-xs">DEMO Admin</p>
          </div>
        </div>

        <nav className="space-y-2">
          <button
            onClick={() => setActiveTab("dashboard")}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
              activeTab === "dashboard" ? "bg-amber-500/20 text-amber-400" : "text-gray-400 hover:bg-white/5"
            }`}
          >
            <LayoutDashboard className="w-5 h-5" />
            Dashboard
          </button>
          <button
            onClick={() => setActiveTab("guests")}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
              activeTab === "guests" ? "bg-amber-500/20 text-amber-400" : "text-gray-400 hover:bg-white/5"
            }`}
          >
            <FileSpreadsheet className="w-5 h-5" />
            Guest Records
          </button>
          <button
            onClick={() => setActiveTab("employees")}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
              activeTab === "employees" ? "bg-amber-500/20 text-amber-400" : "text-gray-400 hover:bg-white/5"
            }`}
          >
            <UserCheck className="w-5 h-5" />
            Employee List
          </button>
          <button
            onClick={() => setActiveTab("settings")}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
              activeTab === "settings" ? "bg-amber-500/20 text-amber-400" : "text-gray-400 hover:bg-white/5"
            }`}
          >
            <Settings className="w-5 h-5" />
            Settings
          </button>
        </nav>

        <div className="absolute bottom-4 left-4 right-4 space-y-2">
          <Button 
            onClick={initializeDemo} 
            disabled={loading}
            className="w-full bg-amber-500 hover:bg-amber-400 text-black"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Reset Demo
          </Button>
          <a href="/demo" className="block">
            <Button variant="outline" className="w-full border-amber-500/50 text-amber-400">
              Guest Portal
            </Button>
          </a>
        </div>
      </div>

      {/* Main Content */}
      <div className="ml-64 p-8">
        {/* Dashboard */}
        {activeTab === "dashboard" && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-6">Demo Dashboard</h2>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <Card className="bg-black/40 border-amber-500/20">
                <CardContent className="p-4 text-center">
                  <Bed className="w-8 h-8 text-amber-400 mx-auto mb-2" />
                  <p className="text-3xl font-bold text-white">{stats.total_rooms}</p>
                  <p className="text-gray-400 text-sm">Total Rooms</p>
                </CardContent>
              </Card>
              <Card className="bg-black/40 border-red-500/20">
                <CardContent className="p-4 text-center">
                  <Users className="w-8 h-8 text-red-400 mx-auto mb-2" />
                  <p className="text-3xl font-bold text-white">{stats.occupied}</p>
                  <p className="text-gray-400 text-sm">Occupied</p>
                </CardContent>
              </Card>
              <Card className="bg-black/40 border-emerald-500/20">
                <CardContent className="p-4 text-center">
                  <DoorOpen className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
                  <p className="text-3xl font-bold text-white">{stats.available}</p>
                  <p className="text-gray-400 text-sm">Available</p>
                </CardContent>
              </Card>
              <Card className="bg-black/40 border-blue-500/20">
                <CardContent className="p-4 text-center">
                  <TrendingUp className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                  <p className="text-3xl font-bold text-white">{stats.occupancy_rate}%</p>
                  <p className="text-gray-400 text-sm">Occupancy</p>
                </CardContent>
              </Card>
            </div>

            <Card className="bg-black/40 border-amber-500/20">
              <CardHeader>
                <CardTitle className="text-amber-400">Currently Checked In</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-slate-700">
                        <th className="text-left p-3 text-amber-400">Room</th>
                        <th className="text-left p-3 text-amber-400">Employee ID</th>
                        <th className="text-left p-3 text-amber-400">Name</th>
                        <th className="text-left p-3 text-amber-400">Check-In</th>
                        <th className="text-left p-3 text-amber-400">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {activeGuests.length === 0 ? (
                        <tr>
                          <td colSpan={5} className="text-center text-gray-500 p-4">No guests checked in</td>
                        </tr>
                      ) : (
                        activeGuests.map((guest) => (
                          <tr key={guest.id} className="border-b border-slate-800">
                            <td className="p-3 text-white font-bold">{guest.room_number}</td>
                            <td className="p-3 text-gray-300">{guest.employee_id}</td>
                            <td className="p-3 text-gray-300">{guest.first_name} {guest.last_name}</td>
                            <td className="p-3 text-gray-400">{new Date(guest.check_in_time).toLocaleString()}</td>
                            <td className="p-3">
                              <span className={`px-2 py-1 rounded text-xs ${guest.is_verified ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'}`}>
                                {guest.is_verified ? 'Verified' : 'Pending'}
                              </span>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Guest Records */}
        {activeTab === "guests" && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-6">Guest Records (Demo)</h2>
            <Card className="bg-black/40 border-amber-500/20">
              <CardContent className="p-4">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-slate-700">
                        <th className="text-left p-3 text-amber-400">Room</th>
                        <th className="text-left p-3 text-amber-400">Employee ID</th>
                        <th className="text-left p-3 text-amber-400">Name</th>
                        <th className="text-left p-3 text-amber-400">Check-In</th>
                        <th className="text-left p-3 text-amber-400">Check-Out</th>
                        <th className="text-left p-3 text-amber-400">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {guests.map((guest) => (
                        <tr key={guest.id} className="border-b border-slate-800">
                          <td className="p-3 text-white font-bold">{guest.room_number}</td>
                          <td className="p-3 text-gray-300">{guest.employee_id}</td>
                          <td className="p-3 text-gray-300">{guest.first_name} {guest.last_name}</td>
                          <td className="p-3 text-gray-400">{new Date(guest.check_in_time).toLocaleString()}</td>
                          <td className="p-3 text-gray-400">{guest.check_out_time ? new Date(guest.check_out_time).toLocaleString() : '-'}</td>
                          <td className="p-3">
                            <span className={`px-2 py-1 rounded text-xs ${guest.is_checked_out ? 'bg-gray-500/20 text-gray-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                              {guest.is_checked_out ? 'Checked Out' : 'In-House'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Employees */}
        {activeTab === "employees" && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-6">Employee List (Demo)</h2>
            <Card className="bg-black/40 border-amber-500/20">
              <CardContent className="p-4">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-slate-700">
                        <th className="text-left p-3 text-amber-400">Employee ID</th>
                        <th className="text-left p-3 text-amber-400">First Name</th>
                        <th className="text-left p-3 text-amber-400">Last Name</th>
                        <th className="text-left p-3 text-amber-400">Craft</th>
                        <th className="text-left p-3 text-amber-400">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {employees.map((emp) => (
                        <tr key={emp.employee_id} className="border-b border-slate-800">
                          <td className="p-3 text-white font-bold">{emp.employee_id}</td>
                          <td className="p-3 text-gray-300">{emp.first_name}</td>
                          <td className="p-3 text-gray-300">{emp.last_name}</td>
                          <td className="p-3 text-gray-400">{emp.craft}</td>
                          <td className="p-3">
                            <span className="px-2 py-1 rounded text-xs bg-emerald-500/20 text-emerald-400">
                              {emp.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Settings */}
        {activeTab === "settings" && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-6">Demo Settings</h2>
            <Card className="bg-black/40 border-amber-500/20">
              <CardContent className="p-6">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
                  <div>
                    <p className="text-amber-400 text-sm mb-1">Railroad Nightly Rate</p>
                    <p className="text-white text-2xl font-bold">${settings.nightly_rate || 75}</p>
                  </div>
                  <div>
                    <p className="text-amber-400 text-sm mb-1">Single Room Rate</p>
                    <p className="text-white text-2xl font-bold">${settings.single_room_rate || 85}</p>
                  </div>
                  <div>
                    <p className="text-amber-400 text-sm mb-1">Double Room Rate</p>
                    <p className="text-white text-2xl font-bold">${settings.double_room_rate || 95}</p>
                  </div>
                  <div>
                    <p className="text-amber-400 text-sm mb-1">Sales Tax</p>
                    <p className="text-white text-2xl font-bold">{settings.sales_tax_rate || 0}%</p>
                  </div>
                  <div>
                    <p className="text-amber-400 text-sm mb-1">Max Chatbot Rooms/Day</p>
                    <p className="text-white text-2xl font-bold">{settings.chatbot_max_rooms || 3}</p>
                  </div>
                  <div>
                    <p className="text-amber-400 text-sm mb-1">Guaranteed Rooms</p>
                    <p className="text-white text-2xl font-bold">{settings.guaranteed_rooms || 25}</p>
                  </div>
                </div>
                <p className="text-gray-500 text-sm mt-6">
                  Demo settings are read-only. Reset demo data to restore defaults.
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-8 text-gray-500 text-sm">
          <p>This is a demo environment. All data is separate from production.</p>
        </div>
      </div>
    </div>
  );
}
