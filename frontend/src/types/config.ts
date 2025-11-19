export interface ProcessingConfig {
  add_bullet_points: boolean;
  add_headers: boolean;
  expand: boolean;
  summarize: boolean;
  focus_topics?: string[];
  latex_style?: 'academic' | 'personal' | 'minimalist';
  font_preference?: string;
  custom_specifications?: string;
  generate_flashcards?: boolean;
  flashcard_topics?: string[];
  flashcard_count?: number;
  max_flashcards_per_topic?: number;
  project_name?: string;
  latex_title?: string;
  include_nickname?: boolean;
  nickname?: string;
}

export const defaultConfig: ProcessingConfig = {
  add_bullet_points: false,
  add_headers: false,
  expand: false,
  summarize: false,
  focus_topics: [],
  latex_style: 'academic',
  font_preference: 'Times New Roman',
  custom_specifications: '',
  generate_flashcards: false,
  flashcard_topics: [],
  flashcard_count: 4,
  max_flashcards_per_topic: 4,
  project_name: '',
  latex_title: '',
  include_nickname: false,
  nickname: '',
};
