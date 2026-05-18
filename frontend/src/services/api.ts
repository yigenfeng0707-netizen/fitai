import axios from 'axios';
import { message } from 'antd';

const API_BASE_URL = '/api/v1';

const instance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

instance.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    } else {
      message.error(error.response?.data?.detail || '请求失败');
    }
    return Promise.reject(error);
  }
);

export const auth = {
  login: (data: { username: string; password: string }) =>
    instance.post('/auth/login', new URLSearchParams(data)),
  register: (data: { username: string; password: string; name: string }) =>
    instance.post('/auth/register', data),
};

export const members = {
  list: (params?: { skip?: number; limit?: number }) =>
    instance.get('/members', { params }),
  get: (id: number) => instance.get(`/members/${id}`),
  create: (data: { name: string; phone: string; email?: string }) =>
    instance.post('/members', data),
  update: (id: number, data: { name?: string; email?: string; status?: string }) =>
    instance.put(`/members/${id}`, data),
  delete: (id: number) => instance.delete(`/members/${id}`),
  cards: (id: number) => instance.get(`/members/${id}/cards`),
  createCard: (id: number, data: { card_no: string; card_type: string; start_date: string }) =>
    instance.post(`/members/${id}/cards`, data),
};

export const courses = {
  list: (params?: { skip?: number; limit?: number }) =>
    instance.get('/courses', { params }),
  get: (id: number) => instance.get(`/courses/${id}`),
  create: (data: { name: string; category_id: number; course_type: string; duration: number; price: number }) =>
    instance.post('/courses', data),
  update: (id: number, data: { name?: string; price?: number }) =>
    instance.put(`/courses/${id}`, data),
  delete: (id: number) => instance.delete(`/courses/${id}`),
  categories: () => instance.get('/courses/categories'),
  createCategory: (data: { name: string }) => instance.post('/courses/categories', data),
  classrooms: () => instance.get('/courses/classrooms'),
  schedules: (params?: { skip?: number; limit?: number }) =>
    instance.get('/courses/schedules', { params }),
  createSchedule: (data: { course_id: number; classroom_id: number; coach_id: number; date: string; start_time: string; end_time: string }) =>
    instance.post('/courses/schedules', data),
};

export const bookings = {
  list: () => instance.get('/bookings'),
  get: (id: number) => instance.get(`/bookings/${id}`),
  create: (data: { schedule_id: number; member_id: number }) =>
    instance.post('/bookings', data),
  cancel: (id: number) => instance.post(`/bookings/${id}/cancel`),
  byMember: (memberId: number) => instance.get(`/bookings/member/${memberId}`),
  bySchedule: (scheduleId: number) => instance.get(`/bookings/schedule/${scheduleId}`),
  attendance: (data: { booking_id: number }) => instance.post('/bookings/attendance', data),
};

export const coaches = {
  list: (params?: { skip?: number; limit?: number }) =>
    instance.get('/coaches', { params }),
  get: (id: number) => instance.get(`/coaches/${id}`),
  create: (data: { name: string; phone?: string; email?: string }) =>
    instance.post('/coaches', data),
  update: (id: number, data: { name?: string; phone?: string }) =>
    instance.put(`/coaches/${id}`, data),
  delete: (id: number) => instance.delete(`/coaches/${id}`),
  schedules: (id: number) => instance.get(`/coaches/${id}/schedules`),
};

export default instance;