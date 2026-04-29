/**
 * 个人主页 API 模块
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => response.data,
  (error) => Promise.reject(error.response?.data || error)
)

export default {
  /**
   * 获取用户个人主页信息
   * @param {number} userId - 用户 ID
   * @returns {Promise}
   */
  getProfile(userId) {
    return api.get(`/profile/${userId}`)
  },

  /**
   * 获取当前用户自己的个人资料
   * @returns {Promise}
   */
  getMyProfile() {
    return api.get('/profile')
  },

  /**
   * 更新当前用户个人资料
   * @param {Object} data - 更新数据
   * @returns {Promise}
   */
  updateProfile(data) {
    return api.put('/profile', data)
  },

  /**
   * 获取用户发布的内容列表
   * @param {number} userId - 用户 ID
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getUserContent(userId, params = {}) {
    return api.get(`/profile/${userId}/posts`, { params })
  },

  /**
   * 获取用户的点赞记录
   * @param {number} userId - 用户 ID
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getUserLikes(userId, params = {}) {
    return api.get(`/profile/${userId}/likes`, { params })
  },

  /**
   * 获取用户统计信息概览
   * @param {number} userId - 用户 ID
   * @returns {Promise}
   */
  getProfileStats(userId) {
    return api.get(`/profile/${userId}/stats`)
  }
}
