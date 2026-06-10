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

export interface Course {
  id: number;
  name: string;
  term: string;
  description?: string | null;
  teacher_id?: number | null;
  status?: string | null;
  created_at?: string | null;
}

export interface Classroom {
  id: number;
  course_id: number;
  name: string;
  invite_code?: string | null;
  student_count: number;
}

export interface Task {
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
  created_by: number;
  created_at?: string | null;
}

export interface Review {
  id: number;
  homework_id: number;
  teacher_id: number;
  student_id?: number | null;
  student_name?: string | null;
  task_id?: number | null;
  task_title?: string | null;
  homework_status?: string | null;
  image_url?: string | null;
  submitted_at?: string | null;
  comment?: string | null;
  final_score?: number | null;
  score?: number | null;
  tags?: string[];
  advice?: string | null;
  compare_image_url?: string | null;
  status: string;
  reviewed_at?: string | null;
}

export interface TagStatItem {
  tag: string;
  category: string;
  count: number;
  ratio: number;
}

export interface DashboardData {
  class_id: number;
  class_name: string;
  student_count: number;
  task_count: number;
  homework_count: number;
  evaluated_count: number;
  avg_score: number;
  submit_rate: number;
  top_issues: string[];
  tag_stats: TagStatItem[];
  top_issue_tags: string[];
  top_positive_tags: string[];
}

export interface ClassReport {
  class_id: number;
  student_count: number;
  task_count: number;
  homework_count: number;
  evaluated_count: number;
  avg_score: number;
}

export interface TaskForm {
  course_id: number | null;
  class_id: number | null;
  title: string;
  description: string;
  practiceChars: string;
  deadline: string;
}

export interface CourseForm {
  name: string;
  term: string;
  description: string;
}

export interface ClassForm {
  name: string;
  inviteCode: string;
}
