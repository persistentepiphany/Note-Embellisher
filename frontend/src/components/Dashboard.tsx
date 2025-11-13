import { Plus, Upload, Filter, Grid3x3, List, Search, LogOut, FileText, Calendar, Clock } from "lucide-react";
import { Button } from "./ui/button";
import { ProjectCard } from "./ProjectCard";
import { FolderCard } from "./FolderCard";
import { EmptyState } from "./EmptyState";
import { Input } from "./ui/input";
import { signOut } from "firebase/auth";
import { auth } from "../firebase";
import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { getAllNotes, NoteResponse, deleteNote, generatePDF } from "../services/apiService";
import { downloadTextFile } from "../utils/exportUtils";
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

  useEffect(() => {
    fetchNotes();
  }, []);



  const handleDownloadNote = (note: NoteResponse) => {
    const content = note.processed_content || note.text || "";
    const filename = `note_${note.id}_${new Date(note.created_at).toISOString().split('T')[0]}.txt`;
    downloadTextFile(content, filename);
  };

  const handleExportNotePDF = async (note: NoteResponse) => {
    try {
      setError(null);
      
      // Check if note has processed content
      if (!note.processed_content) {
        setError('Note must be processed before generating PDF. Please wait for processing to complete.');
        return;
      }
      
      // Call backend to generate LaTeX PDF
      console.log(`Generating LaTeX PDF for note ${note.id}...`);
      const result = await generatePDF(note.id);
      
      // Open the PDF in a new tab
      const pdfUrl = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080'}${result.pdf_url}`;
      window.open(pdfUrl, '_blank');
      
      console.log('PDF generated successfully:', result);
    } catch (error) {
      console.error('Error generating PDF:', error);
      setError(error instanceof Error ? error.message : 'Failed to generate PDF. Please try again.');
    }
  };

  const handleDeleteNote = async (noteId: number) => {
    try {
      console.log('Deleting note with ID:', noteId);
      await deleteNote(noteId);
      console.log('Note deleted successfully');
      await fetchNotes(); // Refresh the notes list
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
                  {notes.map((note) => (
                    <NoteCard
                      key={note.id}
                      note={note}
                      onDownload={handleDownloadNote}
                      onExportPDF={handleExportNotePDF}
                      onDelete={handleDeleteNote}
                    />
                  ))}
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
                  }).map((note) => (
                    <NoteCard
                      key={note.id}
                      note={note}
                      onDownload={handleDownloadNote}
                      onExportPDF={handleExportNotePDF}
                      onDelete={handleDeleteNote}
                    />
                  ))}
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
                  {notes.filter(n => n.status === 'completed').map((note) => (
                    <NoteCard
                      key={note.id}
                      note={note}
                      onDownload={handleDownloadNote}
                      onExportPDF={handleExportNotePDF}
                      onDelete={handleDeleteNote}
                    />
                  ))}
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
                  {notes.filter(n => n.status === 'processing').map((note) => (
                    <NoteCard
                      key={note.id}
                      note={note}
                      onDownload={handleDownloadNote}
                      onExportPDF={handleExportNotePDF}
                      onDelete={handleDeleteNote}
                    />
                  ))}
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
                  {notes.filter(n => n.status === 'error').map((note) => (
                    <NoteCard
                      key={note.id}
                      note={note}
                      onDownload={handleDownloadNote}
                      onExportPDF={handleExportNotePDF}
                      onDelete={handleDeleteNote}
                    />
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>
        )}
      </div>
    </main>
  );
}