export interface ProcessingConfig {
  add_bullet_points: boolean;
  add_headers: boolean;
  expand: boolean;
  summarize: boolean;
  focus_topics?: string[];
  latex_style?: 'academic' | 'personal' | 'minimalist';
  font_preference?: string;
}

export const defaultConfig: ProcessingConfig = {
  add_bullet_points: false,
  add_headers: false,
  expand: false,
  summarize: false,
  focus_topics: [],
  latex_style: 'academic',
  font_preference: 'Times New Roman',
};