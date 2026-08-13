/* LocalFix API Client Module */

const API_BASE = '/api';

class ApiClient {
  constructor() {
    this.token = localStorage.getItem('localfix_token') || null;
    this.user = JSON.parse(localStorage.getItem('localfix_user') || 'null');
  }

  setSession(token, user) {
    this.token = token;
    this.user = user;
    if (token) {
      localStorage.setItem('localfix_token', token);
      localStorage.setItem('localfix_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('localfix_token');
      localStorage.removeItem('localfix_user');
    }
  }

  clearSession() {
    this.setSession(null, null);
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = options.headers || {};
    headers['Content-Type'] = headers['Content-Type'] || 'application/json';

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const config = {
      ...options,
      headers
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        if (response.status === 401) {
          this.clearSession();
          window.dispatchEvent(new CustomEvent('auth:unauthorized'));
        } else if (response.status === 403) {
          window.dispatchEvent(new CustomEvent('auth:forbidden', { detail: data }));
        }
        throw new Error(data.error || `HTTP Error ${response.status}`);
      }

      return data;
    } catch (err) {
      console.error(`API Request Error [${endpoint}]:`, err);
      throw err;
    }
  }

  // Auth endpoints
  login(email, password) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
  }

  signup(formData) {
    return this.request('/auth/signup', {
      method: 'POST',
      body: JSON.stringify(formData)
    });
  }

  getMe() {
    return this.request('/auth/me');
  }

  // Categories
  getCategories() {
    return this.request('/categories');
  }

  // Providers
  searchProviders(params = {}) {
    const query = new URLSearchParams();
    Object.keys(params).forEach(k => {
      if (params[k] !== undefined && params[k] !== null && params[k] !== '') {
        query.append(k, params[k]);
      }
    });
    return this.request(`/providers/search?${query.toString()}`);
  }

  getProviderProfile(id) {
    return this.request(`/providers/${id}`);
  }

  updateAvailability(status) {
    return this.request('/providers/availability', {
      method: 'PUT',
      body: JSON.stringify({ availability_status: status })
    });
  }

  updateProviderProfile(profileData) {
    return this.request('/providers/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData)
    });
  }

  // Bookings
  createBooking(bookingData) {
    return this.request('/bookings', {
      method: 'POST',
      body: JSON.stringify(bookingData)
    });
  }

  getBookings(status = null) {
    const q = status ? `?status=${status}` : '';
    return this.request(`/bookings${q}`);
  }

  getBooking(id) {
    return this.request(`/bookings/${id}`);
  }

  updateBookingStatus(id, status, reason = '') {
    return this.request(`/bookings/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status, reason })
    });
  }

  cancelBooking(id, reason) {
    return this.request(`/bookings/${id}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ reason })
    });
  }

  // Reviews
  createReview(reviewData) {
    return this.request('/reviews', {
      method: 'POST',
      body: JSON.stringify(reviewData)
    });
  }

  getProviderReviews(providerId) {
    return this.request(`/reviews/provider/${providerId}`);
  }

  // Reports
  createReport(reportData) {
    return this.request('/reports', {
      method: 'POST',
      body: JSON.stringify(reportData)
    });
  }

  // Admin Endpoints
  getAdminStats() {
    return this.request('/admin/stats');
  }

  getAdminProviders(status = null) {
    const q = status ? `?status=${status}` : '';
    return this.request(`/admin/providers${q}`);
  }

  verifyProvider(providerId, status) {
    return this.request(`/admin/providers/${providerId}/verify`, {
      method: 'PATCH',
      body: JSON.stringify({ status })
    });
  }

  getAdminUsers(role = null) {
    const q = role ? `?role=${role}` : '';
    return this.request(`/admin/users${q}`);
  }

  deleteUser(userId) {
    return this.request(`/admin/users/${userId}`, {
      method: 'DELETE'
    });
  }

  createCategory(categoryData) {
    return this.request('/admin/categories', {
      method: 'POST',
      body: JSON.stringify(categoryData)
    });
  }

  updateCategory(id, categoryData) {
    return this.request(`/admin/categories/${id}`, {
      method: 'PUT',
      body: JSON.stringify(categoryData)
    });
  }

  getAdminReports() {
    return this.request('/admin/reports');
  }

  updateReportStatus(id, status) {
    return this.request(`/admin/reports/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ status })
    });
  }

  getAdminReviews() {
    return this.request('/admin/reviews');
  }

  deleteReview(id) {
    return this.request(`/admin/reviews/${id}`, {
      method: 'DELETE'
    });
  }
}

window.api = new ApiClient();
