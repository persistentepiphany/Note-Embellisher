import { Plus, Upload, Grid3x3, List, Search, LogOut, FileText, Calendar, Clock, Cloud } from "lucide-react";
import { Button } from "./ui/button";
import { EmptyState } from "./EmptyState";
import { Input } from "./ui/input";
import { signOut } from "firebase/auth";
import { auth } from "../firebase";
import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import {
  getAllNotes,
  NoteResponse,
  deleteNote,
  generatePDF,
  generateDocx,
  generateTxt,
  uploadNoteToDrive,
  getGoogleDriveStatus,
  getGoogleDriveAuthUrl,
  API_BASE_URL,
} from "../services/apiService";
import { NoteCard } from "./NoteCard";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Card, CardContent } from "./ui/card";

// Empty arrays for new user with no content
const sampleProjects: any[] = [];
const sampleFolders: any[] = [];

export function Dashboard() {
  const navigate = useNavigate();
  const [notes, setNotes] = useState<NoteResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [driveConnected, setDriveConnected] = useState(false);
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [connectingDrive, setConnectingDrive] = useState(false);

  const handleSignOut = async () => {
    try {
      await signOut(auth);
      console.log("User signed out successfully");
    } catch (error) {
      console.error("Error signing out:", error);
    }
  };

  const handleCreateNew = () => {
    navigate('/note-submission');
  };

  const fetchNotes = async () => {
    try {
      setLoading(true);
      setError(null);
      setStatusMessage(null);
      const fetchedNotes = await getAllNotes();
      
      // Ensure all notes have valid structure to prevent rendering errors
      const validNotes = fetchedNotes.map(note => ({
        ...note,
        text: note.text ?? '',
        processed_content: note.processed_content ?? null,
        settings: note.settings ?? {
          add_bullet_points: false,
          add_headers: false,
          expand: false,
          summarize: false
        }
      }));
      
      setNotes(validNotes);
    } catch (err) {
      console.error('Error fetching notes:', err);
      setError(err instanceof Error ? err.message : 'Failed to load notes');
    } finally {
      setLoading(false);
    }
  };

  const checkDriveStatus = async () => {
    try {
      const status = await getGoogleDriveStatus();
      setDriveConnected(status.connected);
    } catch (err) {
      console.warn('Google Drive status unavailable:', err);
    }
  };

  useEffect(() => {
    fetchNotes();
    checkDriveStatus();
  }, []);

  const updateNote = (noteId: number, updates: Partial<NoteResponse>) => {
    setNotes(prev => prev.map(note => (note.id === noteId ? { ...note, ...updates } : note)));
  };

  const makeFileUrl = (path?: string | null) => {
    if (!path) return null;
    return `${API_BASE_URL}${path}`;
  };

  const runAction = async (noteId: number, action: string, fn: () => Promise<void>) => {
    setPendingAction(`${action}-${noteId}`);
    setStatusMessage(null);
    try {
      await fn();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Something went wrong. Please try again.';
      setError(message);
      throw err;
    } finally {
      setPendingAction(null);
    }
  };

  const isActionPending = (noteId: number, action: string) => pendingAction === `${action}-${noteId}`;

  const ensurePdfUrl = async (note: NoteResponse) => {
    if (note.pdf_url) return note.pdf_url;
    const result = await generatePDF(note.id);
    updateNote(note.id, { pdf_url: result.pdf_url });
    return result.pdf_url;
  };

  const ensureDocxUrl = async (note: NoteResponse) => {
    if (note.docx_url) return note.docx_url;
    const result = await generateDocx(note.id);
    updateNote(note.id, { docx_url: result.docx_url });
    return result.docx_url;
  };

  const ensureTxtUrl = async (note: NoteResponse) => {
    if (note.txt_url) return note.txt_url;
    const result = await generateTxt(note.id);
    updateNote(note.id, { txt_url: result.txt_url });
    return result.txt_url;
  };

  const handleDownloadPdf = async (note: NoteResponse) => {
    if (note.status !== 'completed') {
      setError('Note is still processing. Please wait until it is completed.');
      return;
    }
    try {
      await runAction(note.id, 'pdf', async () => {
        const pdfRelativeUrl = await ensurePdfUrl(note);
        const fullUrl = makeFileUrl(pdfRelativeUrl);
        if (!fullUrl) {
          throw new Error('PDF file is not ready yet.');
        }
        window.open(fullUrl, '_blank', 'noopener');
        setError(null);
      });
    } catch {
      // Error handled in runAction
    }
  };

  const handleDownloadDocx = async (note: NoteResponse) => {
    if (note.status !== 'completed') {
      setError('Note is still processing. Please wait until it is completed.');
      return;
    }
    try {
      await runAction(note.id, 'docx', async () => {
        const docxRelativeUrl = await ensureDocxUrl(note);
        const fullUrl = makeFileUrl(docxRelativeUrl);
        if (!fullUrl) {
          throw new Error('Word document is not ready yet.');
        }
        window.open(fullUrl, '_blank', 'noopener');
        setError(null);
      });
    } catch {
      // handled
    }
  };

  const handleDownloadTxt = async (note: NoteResponse) => {
    if (note.status !== 'completed') {
      setError('Note is still processing. Please wait until it is completed.');
      return;
    }
    try {
      await runAction(note.id, 'txt', async () => {
        const txtRelativeUrl = await ensureTxtUrl(note);
        const fullUrl = makeFileUrl(txtRelativeUrl);
        if (!fullUrl) {
          throw new Error('TXT file is not ready yet.');
        }
        window.open(fullUrl, '_blank', 'noopener');
        setError(null);
      });
    } catch {
      // handled
    }
  };

  const waitForDriveConnection = async () => {
    for (let attempt = 0; attempt < 15; attempt++) {
      await new Promise(resolve => setTimeout(resolve, 2000));
      try {
        const status = await getGoogleDriveStatus();
        if (status.connected) {
          setDriveConnected(true);
          return true;
        }
      } catch (err) {
        console.warn('Unable to check Drive status during auth:', err);
        break;
      }
    }
    return false;
  };

  const startDriveAuthFlow = async () => {
    const { auth_url } = await getGoogleDriveAuthUrl();
    const popup = window.open(auth_url, 'drive-auth', 'width=520,height=720');
    const connected = await waitForDriveConnection();
    popup?.close();
    if (!connected) {
      throw new Error('Google Drive connection timed out. Please try again.');
    }
  };

  const handleDriveUpload = async (note: NoteResponse, format: 'pdf' | 'docx' | 'txt') => {
    if (note.status !== 'completed') {
      setError('Note is still processing. Please wait until it is completed.');
      return;
    }
    try {
      await runAction(note.id, 'drive', async () => {
        try {
          await uploadNoteToDrive(note.id, format);
          setError(null);
          setStatusMessage('Uploaded to Google Drive successfully.');
          setDriveConnected(true);
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Failed to upload to Google Drive.';
          if (message.toLowerCase().includes('not connected')) {
            await startDriveAuthFlow();
            await uploadNoteToDrive(note.id, format);
            setStatusMessage('Google Drive connected and file uploaded successfully.');
          } else {
            throw new Error(message);
          }
        }
      });
    } catch {
      // handled by runAction
    }
  };

  const handleConnectDrive = async () => {
    setError(null);
    setStatusMessage(null);
    setConnectingDrive(true);
    try {
      await startDriveAuthFlow();
      setStatusMessage('Google Drive connected successfully.');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to connect Google Drive.';
      setError(message);
    } finally {
      setConnectingDrive(false);
    }
  };

  const renderNoteCard = (note: NoteResponse) => (
    <NoteCard
      key={note.id}
      note={note}
      apiBaseUrl={API_BASE_URL}
      onDownloadPdf={handleDownloadPdf}
      onDownloadDocx={handleDownloadDocx}
      onDownloadTxt={handleDownloadTxt}
      onUploadToDrive={handleDriveUpload}
      onDelete={handleDeleteNote}
      actionStates={{
        pdf: isActionPending(note.id, 'pdf'),
        docx: isActionPending(note.id, 'docx'),
        txt: isActionPending(note.id, 'txt'),
        drive: isActionPending(note.id, 'drive'),
      }}
    />
  );

  const handleDeleteNote = async (noteId: number) => {
    try {
      console.log('Deleting note with ID:', noteId);
      await deleteNote(noteId);
      console.log('Note deleted successfully');
      await fetchNotes(); // Refresh the notes list
      setStatusMessage('Note deleted successfully.');
    } catch (error) {
      console.error('Error deleting note:', error);
      setError(error instanceof Error ? error.message : 'Failed to delete note');
    }
  };

  return (
    <main className="flex-1 overflow-auto">
      <div className="p-6">
        {/* Header Section */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-medium mb-2">Dashboard</h1>
            <p className="text-muted-foreground">
              Welcome to Note Embellisher! Start by creating your first project to organize your notes.
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            <Button
              variant={driveConnected ? "secondary" : "outline"}
              size="sm"
              onClick={handleConnectDrive}
              disabled={connectingDrive}
            >
              <Cloud className="w-4 h-4 mr-2" />
              {driveConnected ? 'Drive Connected' : connectingDrive ? 'Connecting...' : 'Connect Drive'}
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleSignOut}
              className="text-red-600 hover:text-red-700 hover:border-red-300"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Sign Out
            </Button>
            <Button variant="outline" size="sm">
              <Upload className="w-4 h-4 mr-2" />
              Import
            </Button>
            <Button size="sm" onClick={handleCreateNew}>
              <Plus className="w-4 h-4 mr-2" />
              Create New
            </Button>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Notes</p>
                  <p className="text-2xl font-medium">{notes.length}</p>
                </div>
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <FileText className="w-4 h-4 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Completed</p>
                  <p className="text-2xl font-medium">{notes.filter(n => n.status === 'completed').length}</p>
                </div>
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <Search className="w-4 h-4 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Processing</p>
                  <p className="text-2xl font-medium">{notes.filter(n => n.status === 'processing').length}</p>
                </div>
                <div className="w-8 h-8 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <Clock className="w-4 h-4 text-yellow-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Recent</p>
                  <p className="text-2xl font-medium">{notes.filter(n => {
                    const dayAgo = new Date();
                    dayAgo.setDate(dayAgo.getDate() - 1);
                    return new Date(n.created_at) > dayAgo;
                  }).length}</p>
                </div>
                <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Calendar className="w-4 h-4 text-purple-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filter and Search Bar */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                placeholder="Search notes..."
                className="pl-10 w-80 bg-input-background border-0"
              />
            </div>
            <Select defaultValue="all">
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="processing">Processing</SelectItem>
                <SelectItem value="error">Error</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm" onClick={fetchNotes}>
              <Upload className="w-4 h-4 mr-2" />
              Refresh
            </Button>
            <Button variant="outline" size="sm">
              <Grid3x3 className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm">
              <List className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Notes Section */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="relative">
              <div className="w-8 h-8 border-2 border-orange-200 border-t-orange-500 rounded-full animate-spin"></div>
            </div>
            <span className="ml-3 text-gray-600">Loading notes...</span>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-700">{error}</p>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={fetchNotes}
              className="mt-2"
            >
              Try Again
            </Button>
          </div>
        ) : (
          <>
            {statusMessage && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-6 text-green-800">
                {statusMessage}
              </div>
            )}
            <Tabs defaultValue="all" className="w-full">
            <TabsList className="mb-6">
              <TabsTrigger value="all">All Notes</TabsTrigger>
              <TabsTrigger value="recent">Recent</TabsTrigger>
              <TabsTrigger value="completed">Completed</TabsTrigger>
              <TabsTrigger value="processing">Processing</TabsTrigger>
              <TabsTrigger value="error">Errors</TabsTrigger>
            </TabsList>

            <TabsContent value="all">
              {notes.length === 0 ? (
                <EmptyState type="projects" />
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {notes.map(note => renderNoteCard(note))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="recent">
              {notes.filter(n => {
                const dayAgo = new Date();
                dayAgo.setDate(dayAgo.getDate() - 1);
                return new Date(n.created_at) > dayAgo;
              }).length === 0 ? (
                <EmptyState type="recent" />
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {notes.filter(n => {
                    const dayAgo = new Date();
                    dayAgo.setDate(dayAgo.getDate() - 1);
                    return new Date(n.created_at) > dayAgo;
                  }).map(note => renderNoteCard(note))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="completed">
              {notes.filter(n => n.status === 'completed').length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-600 mb-2">No completed notes yet</h3>
                  <p className="text-gray-500 mb-4">Your processed notes will appear here once they're ready.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {notes.filter(n => n.status === 'completed').map(note => renderNoteCard(note))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="processing">
              {notes.filter(n => n.status === 'processing').length === 0 ? (
                <div className="text-center py-12">
                  <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-600 mb-2">No notes processing</h3>
                  <p className="text-gray-500 mb-4">Notes being processed will appear here.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {notes.filter(n => n.status === 'processing').map(note => renderNoteCard(note))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="error">
              {notes.filter(n => n.status === 'error').length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-600 mb-2">No errors</h3>
                  <p className="text-gray-500 mb-4">Notes that failed to process will appear here.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {notes.filter(n => n.status === 'error').map(note => renderNoteCard(note))}
                </div>
              )}
            </TabsContent>
          </Tabs>
          </>
        )}
      </div>
    </main>
  );
}