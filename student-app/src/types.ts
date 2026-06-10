export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

export interface CurrentUser {
  id: number;
  username: string;
  name: string;
  role: string;
  school_name?: string | null;
  avatar_url?: string | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: CurrentUser;
}

export interface Classroom {
  id: number;
  course_id: number;
  name: string;
  invite_code?: string | null;
  student_count: number;
}

export interface StudentTask {
  id: number;
  course_id: number;
  class_id: number;
  title: string;
  description?: string | null;
  practice_chars: string[];
  structure_weight: number;
  center_weight: number;
  stroke_order_weight: number;
  deadline?: string | null;
}

export interface Homework {
  id: number;
  task_id: number;
  student_id: number;
  status: string;
  image_url: string;
  processed_image_url?: string | null;
  submitted_at?: string | null;
}

export interface HomeworkUploadResult {
  homework_id: number;
  file_url: string;
  status: string;
}

export interface Evaluation {
  id: number;
  homework_id: number;
  score: number;
  total_score: number;
  structure_score: number;
  center_score: number;
  stroke_order_score: number;
  stroke_quality_score?: number;
  tags: string[];
  issues: string[];
  advice?: string | null;
  compare_image_url?: string | null;
  thinking_steps?: ThinkingStep[] | null;
  status: string;
  created_at?: string | null;
  calligraphy_images?: string[];
}

export interface ThinkingStep {
  step: number;
  title: string;
  detail: string;
  status: "pending" | "running" | "done";
  score?: number | null;
}

export interface Growth {
  user_id: number;
  avg_score: number;
  recent_scores?: number[];
  recent_labels?: string[];
}

export interface TaskSubmitForm {
  imageUrl: string;
  selectedFileName?: string;
}

export interface TagTrendRecord {
  homework_id: number;
  created_at: string;
  score: number;
  tags: string[];
}

export interface FrequentIssueTag {
  tag: string;
  count: number;
}

export interface ImprovedTag {
  tag: string;
  previous_count: number;
  recent_count: number;
}

export interface StudentTagTrend {
  student_id: number;
  records: TagTrendRecord[];
  frequent_issue_tags: FrequentIssueTag[];
  improved_tags: ImprovedTag[];
}
