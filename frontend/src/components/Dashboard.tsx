import { Plus, Upload, Filter, Grid3x3, List, Search, LogOut } from "lucide-react";
import { Button } from "./ui/button";
import { ProjectCard } from "./ProjectCard";
import { FolderCard } from "./FolderCard";
import { EmptyState } from "./EmptyState";
import { Input } from "./ui/input";
import { signOut } from "firebase/auth";
import { auth } from "../firebase";
import { useNavigate } from "react-router-dom";
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
                  <p className="text-sm text-muted-foreground">Total Projects</p>
                  <p className="text-2xl font-medium">{sampleProjects.length}</p>
                </div>
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Grid3x3 className="w-4 h-4 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Favorites</p>
                  <p className="text-2xl font-medium">{sampleProjects.filter(p => p.isFavorite).length}</p>
                </div>
                <div className="w-8 h-8 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <Search className="w-4 h-4 text-yellow-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Pages</p>
                  <p className="text-2xl font-medium">{sampleProjects.reduce((acc, p) => acc + p.pageCount, 0)}</p>
                </div>
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <List className="w-4 h-4 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Folders</p>
                  <p className="text-2xl font-medium">{sampleFolders.length}</p>
                </div>
                <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Filter className="w-4 h-4 text-purple-600" />
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
                placeholder="Search projects..."
                className="pl-10 w-80 bg-input-background border-0"
              />
            </div>
            <Select defaultValue="all">
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="research">Research</SelectItem>
                <SelectItem value="business">Business</SelectItem>
                <SelectItem value="education">Education</SelectItem>
                <SelectItem value="personal">Personal</SelectItem>
                <SelectItem value="lifestyle">Lifestyle</SelectItem>
                <SelectItem value="health">Health</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm">
              <Grid3x3 className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm">
              <List className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Projects Section */}
        <Tabs defaultValue="all" className="w-full">
          <TabsList className="mb-6">
            <TabsTrigger value="all">All Projects</TabsTrigger>
            <TabsTrigger value="recent">Recent</TabsTrigger>
            <TabsTrigger value="favorites">Favorites</TabsTrigger>
            <TabsTrigger value="folders">View Folders</TabsTrigger>
          </TabsList>

          <TabsContent value="all">
            {sampleProjects.length === 0 ? (
              <EmptyState type="projects" />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {sampleProjects.map((project) => (
                  <ProjectCard key={project.id} {...project} />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="recent">
            {sampleProjects.length === 0 ? (
              <EmptyState type="recent" />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {sampleProjects.slice(0, 1).map((project) => (
                  <ProjectCard key={project.id} {...project} />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="favorites">
            {sampleProjects.filter(p => p.isFavorite).length === 0 ? (
              <EmptyState type="favorites" />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {sampleProjects.filter(p => p.isFavorite).map((project) => (
                  <ProjectCard key={project.id} {...project} />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="folders">
            {sampleFolders.length === 0 ? (
              <EmptyState type="folders" />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {sampleFolders.map((folder) => (
                  <FolderCard key={folder.id} {...folder} />
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </main>
  );
}