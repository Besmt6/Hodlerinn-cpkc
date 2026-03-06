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
  LogIn, 
  LogOut,
  RefreshCw,
  Settings,
  Bed,
  CheckCircle,
  XCircle
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api/demo`;

export default function DemoPortal() {
  const [rooms, setRooms] = useState([]);
  const [stats, setStats] = useState({ total_rooms: 28, occupied: 0, available: 28, occupancy_rate: 0 });
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [employeeId, setEmployeeId] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [roomsRes, statsRes] = await Promise.all([
        axios.get(`${API}/rooms`),
        axios.get(`${API}/stats`)
      ]);
      setRooms(roomsRes.data);
      setStats(statsRes.data);
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

  const handleCheckin = async () => {
    if (!selectedRoom || !employeeId) {
      toast.error("Please select a room and enter employee ID");
      return;
    }
    try {
      await axios.post(`${API}/checkin?employee_id=${employeeId}&room_number=${selectedRoom}&first_name=${firstName}&last_name=${lastName}`);
      toast.success(`Checked in to room ${selectedRoom}`);
      setSelectedRoom(null);
      setEmployeeId("");
      setFirstName("");
      setLastName("");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Check-in failed");
    }
  };

  const handleCheckout = async (roomNumber) => {
    try {
      await axios.post(`${API}/checkout?room_number=${roomNumber}`);
      toast.success(`Checked out of room ${roomNumber}`);
      fetchData();
    } catch (error) {
      toast.error("Check-out failed");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-gradient-to-br from-amber-400 to-amber-600 rounded-full flex items-center justify-center">
              <Home className="w-6 h-6 text-black" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Hodler Inn Demo</h1>
              <p className="text-amber-400 text-sm">Guest Portal - Test Environment</p>
            </div>
          </div>
          <div className="flex gap-3">
            <Button 
              onClick={initializeDemo} 
              disabled={loading}
              className="bg-amber-500 hover:bg-amber-400 text-black"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Reset Demo Data
            </Button>
            <a href="/demo/admin">
              <Button variant="outline" className="border-amber-500/50 text-amber-400 hover:bg-amber-500/10">
                <Settings className="w-4 h-4 mr-2" />
                Admin Demo
              </Button>
            </a>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto">
        {/* Stats */}
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
              <p className="text-3xl font-bold text-white">{stats.occupancy_rate}%</p>
              <p className="text-gray-400 text-sm">Occupancy</p>
            </CardContent>
          </Card>
        </div>

        {/* Check-in Form */}
        <Card className="bg-black/40 border-amber-500/20 mb-8">
          <CardHeader>
            <CardTitle className="text-amber-400 flex items-center gap-2">
              <LogIn className="w-5 h-5" />
              Demo Check-In
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <Input
                placeholder="Employee ID"
                value={employeeId}
                onChange={(e) => setEmployeeId(e.target.value)}
                className="bg-black/50 border-slate-700 text-white"
              />
              <Input
                placeholder="First Name"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className="bg-black/50 border-slate-700 text-white"
              />
              <Input
                placeholder="Last Name"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className="bg-black/50 border-slate-700 text-white"
              />
              <Input
                placeholder="Room #"
                value={selectedRoom || ""}
                onChange={(e) => setSelectedRoom(parseInt(e.target.value) || null)}
                className="bg-black/50 border-slate-700 text-white"
              />
              <Button onClick={handleCheckin} className="bg-emerald-600 hover:bg-emerald-500">
                <LogIn className="w-4 h-4 mr-2" />
                Check In
              </Button>
            </div>
            <p className="text-gray-500 text-xs mt-2">Or click on an available room below to select it</p>
          </CardContent>
        </Card>

        {/* Room Grid */}
        <Card className="bg-black/40 border-amber-500/20">
          <CardHeader>
            <CardTitle className="text-amber-400">Room Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 sm:grid-cols-7 md:grid-cols-10 gap-3">
              {rooms.map((room) => (
                <div
                  key={room.room_number}
                  onClick={() => !room.is_occupied && setSelectedRoom(room.room_number)}
                  className={`
                    p-3 rounded-lg text-center cursor-pointer transition-all
                    ${room.is_occupied 
                      ? 'bg-red-500/20 border border-red-500/50' 
                      : selectedRoom === room.room_number
                        ? 'bg-amber-500/30 border-2 border-amber-500'
                        : 'bg-emerald-500/20 border border-emerald-500/50 hover:bg-emerald-500/30'
                    }
                  `}
                >
                  <p className="text-white font-bold">{room.room_number}</p>
                  <p className="text-xs text-gray-400">{room.room_type}</p>
                  {room.is_occupied && (
                    <Button
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCheckout(room.room_number);
                      }}
                      className="mt-2 bg-red-600 hover:bg-red-500 text-xs px-2 py-1 h-auto"
                    >
                      <LogOut className="w-3 h-3 mr-1" />
                      Out
                    </Button>
                  )}
                </div>
              ))}
            </div>
            <div className="flex gap-6 mt-6 justify-center text-sm">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-emerald-500/30 border border-emerald-500 rounded"></div>
                <span className="text-gray-400">Available</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-red-500/30 border border-red-500 rounded"></div>
                <span className="text-gray-400">Occupied</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-amber-500/30 border-2 border-amber-500 rounded"></div>
                <span className="text-gray-400">Selected</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center mt-8 text-gray-500 text-sm">
          <p>This is a demo environment. All data is separate from production.</p>
          <p className="mt-2">
            <a href="/book" className="text-amber-400 hover:underline">Try Bitsy Chatbot</a>
            {" | "}
            <a href="/" className="text-amber-400 hover:underline">Production Portal</a>
          </p>
        </div>
      </div>
    </div>
  );
}
