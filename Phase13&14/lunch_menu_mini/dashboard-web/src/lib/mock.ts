/**
 * Mock seed data — ported from legacy jsx.
 * Replace with real API calls once lunch-optimizer endpoints are wired.
 */
import type {
  Restaurant,
  TeamMember,
  WeeklyNutritionDay,
  WeatherNow,
} from "./types";

export const RESTAURANTS: Restaurant[] = [
  { id: 1, name: "한솥도시락", category: "한식", distance: 120, rating: 4.2, price: 6500, indoor: true, menuType: "밥류", calories: 650, protein: 28, carbs: 85, fat: 18, visits: 12, lastVisit: "2026-03-28" },
  { id: 2, name: "스시로", category: "일식", distance: 350, rating: 4.5, price: 12000, indoor: true, menuType: "초밥", calories: 520, protein: 32, carbs: 65, fat: 12, visits: 5, lastVisit: "2026-04-01" },
  { id: 3, name: "팔당냉면", category: "한식", distance: 200, rating: 4.3, price: 9000, indoor: true, menuType: "면류", calories: 480, protein: 18, carbs: 72, fat: 8, visits: 8, lastVisit: "2026-03-25" },
  { id: 4, name: "맥도날드", category: "양식", distance: 150, rating: 3.8, price: 7500, indoor: true, menuType: "패스트푸드", calories: 780, protein: 35, carbs: 68, fat: 42, visits: 15, lastVisit: "2026-04-03" },
  { id: 5, name: "베트남쌀국수", category: "동남아", distance: 280, rating: 4.1, price: 8500, indoor: true, menuType: "국물", calories: 420, protein: 22, carbs: 58, fat: 10, visits: 3, lastVisit: "2026-03-20" },
  { id: 6, name: "교촌치킨", category: "한식", distance: 400, rating: 4.4, price: 11000, indoor: true, menuType: "치킨", calories: 720, protein: 42, carbs: 45, fat: 38, visits: 6, lastVisit: "2026-03-30" },
  { id: 7, name: "서브웨이", category: "양식", distance: 180, rating: 4.0, price: 7000, indoor: true, menuType: "샌드위치", calories: 380, protein: 24, carbs: 48, fat: 14, visits: 10, lastVisit: "2026-04-02" },
  { id: 8, name: "명동칼국수", category: "한식", distance: 320, rating: 4.6, price: 8000, indoor: true, menuType: "국물", calories: 550, protein: 20, carbs: 78, fat: 15, visits: 7, lastVisit: "2026-03-22" },
  { id: 9, name: "매드포갈릭", category: "양식", distance: 500, rating: 4.3, price: 15000, indoor: true, menuType: "파스타", calories: 680, protein: 26, carbs: 82, fat: 28, visits: 2, lastVisit: "2026-03-15" },
  { id: 10, name: "김밥천국", category: "한식", distance: 80, rating: 3.6, price: 5000, indoor: true, menuType: "밥류", calories: 520, protein: 16, carbs: 75, fat: 16, visits: 20, lastVisit: "2026-04-04" },
  { id: 11, name: "쉑쉑버거", category: "양식", distance: 450, rating: 4.2, price: 13000, indoor: true, menuType: "버거", calories: 850, protein: 38, carbs: 62, fat: 48, visits: 4, lastVisit: "2026-03-18" },
  { id: 12, name: "본죽", category: "한식", distance: 160, rating: 4.1, price: 8000, indoor: true, menuType: "죽", calories: 320, protein: 14, carbs: 55, fat: 6, visits: 9, lastVisit: "2026-04-01" },
];

export const WEATHER: WeatherNow = {
  temp: 12,
  humidity: 55,
  dust: "보통",
  sky: "흐림",
  rain: 30,
};

export const TEAM: TeamMember[] = [
  { id: "user1", name: "김민수", vote: null, avatar: "🧑‍💻" },
  { id: "user2", name: "이수진", vote: null, avatar: "👩‍💼" },
  { id: "user3", name: "박준혁", vote: null, avatar: "👨‍🔬" },
  { id: "user4", name: "정하은", vote: null, avatar: "👩‍🎨" },
  { id: "user5", name: "최동원", vote: null, avatar: "🧑‍🏫" },
];

export const WEEKLY_NUTRITION: WeeklyNutritionDay[] = [
  { day: "월", calories: 680, protein: 28, carbs: 85, fat: 22, target: 700 },
  { day: "화", calories: 520, protein: 32, carbs: 60, fat: 14, target: 700 },
  { day: "수", calories: 780, protein: 35, carbs: 70, fat: 42, target: 700 },
  { day: "목", calories: 450, protein: 22, carbs: 58, fat: 12, target: 700 },
  { day: "금", calories: 0, protein: 0, carbs: 0, fat: 0, target: 700 },
];

export const CATEGORY_COLORS: Record<string, string> = {
  한식: "#E8593C",
  일식: "#3B8BD4",
  양식: "#639922",
  중식: "#BA7517",
  동남아: "#1D9E75",
};
