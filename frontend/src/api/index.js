import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 180000  // 3 分钟超时，支持 AI 慢响应
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

// 防止重复跳转
let isRedirecting = false
const resetRedirectFlag = () => { setTimeout(() => { isRedirecting = false }, 3000) }

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401 && !isRedirecting) {
      isRedirecting = true
      // Token 失效，清除本地存储
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('portal_username')
      localStorage.removeItem('portal_token')
      // 如果当前已经在登录页，不需要重复跳转
      if (window.location.pathname === '/login' || window.location.pathname === '/portal/login') {
        resetRedirectFlag()
        return Promise.reject(error.response?.data || error)
      }
      const redirectPath = window.location.pathname
      const redirect = redirectPath.startsWith('/login') ? '' : `?redirect=${encodeURIComponent(redirectPath)}`
      window.location.href = `/login${redirect}`
      return Promise.reject(error.response?.data || error)
    }
    return Promise.reject(error.response?.data || error)
  }
)

export default {
  // 认证
  login(data) {
    return api.post('/auth/login', data)
  },

  register(data) {
    return api.post('/auth/register', data)
  },

  // 仪表板
  getDashboardData() {
    return api.get('/dashboard')
  },

  getKPIs() {
    return api.get('/kpis')
  },

  getSalesTrend(params) {
    return api.get('/sales/trend', { params })
  },

  // 数据预览
  getTableData(table, params) {
    return api.get(`/data/${table}`, { params })
  },

  listTables() {
    return api.get('/data/tables')
  },

  // ETL 任务
  getETLTasks() {
    return api.get('/etl/tasks')
  },

  runETLTask(taskId) {
    return api.post(`/etl/tasks/${taskId}/run`)
  },

  getETLLog(taskId) {
    return api.get(`/etl/tasks/${taskId}/log`)
  },

  // AI 智能问数
  aiQuery: {
    generate(question) {
      return api.post('/ai-query/generate-sql', { question })
    },

    execute(question, topK = 10) {
      return api.post('/ai-query/execute-query', { question, top_k: topK })
    },

    getSchema() {
      return api.get('/ai-query/schema')
    }
  },

  // 报表接口
  reports: {
    // 销售 KPI 汇总
    getKpiSummary() {
      return api.get('/reports/sales/kpi-summary')
    },

    // 销售趋势
    getSalesTrend(params) {
      return api.get('/reports/sales/trend', { params })
    },

    // 产品排行
    getProductRanking(params) {
      return api.get('/reports/sales/product-ranking', { params })
    },

    // 品类分析
    getCategoryAnalysis() {
      return api.get('/reports/sales/category-analysis')
    },

    // 客户分析
    getCustomerAnalysis() {
      return api.get('/reports/customer/analysis')
    }
  },

  // 通用
  health() {
    return api.get('/health')
  },

  // 点赞功能
  likes: {
    // 点赞
    like(data) {
      return api.post('/likes', data)
    },

    // 取消点赞
    unlike(targetType, targetId) {
      return api.delete('/likes', { params: { target_type: targetType, target_id: targetId } })
    },

    // 获取点赞状态
    getStatus(targetType, targetId) {
      return api.get('/likes/status', { params: { target_type: targetType, target_id: targetId } })
    },

    // 获取点赞数量
    getCount(targetType, targetId) {
      return api.get('/likes/count', { params: { target_type: targetType, target_id: targetId } })
    },

    // 获取点赞用户列表
    getLikers(targetType, targetId, limit = 20, offset = 0) {
      return api.get('/likes/list', { params: { target_type: targetType, target_id: targetId, limit, offset } })
    },

    // 获取我的点赞列表
    getMyLikes(targetType = null, limit = 20, offset = 0) {
      const params = { limit, offset }
      if (targetType) {
        params.target_type = targetType
      }
      return api.get('/likes/my', { params })
    }
  },

  // 关注功能
  follows: {
    // 关注
    follow(data) {
      return api.post('/follows', data)
    },

    // 取消关注
    unfollow(followedId) {
      return api.delete('/follows', { params: { followed_id: followedId } })
    },

    // 获取关注状态
    getStatus(userId) {
      return api.get('/follows/status', { params: { user_id: userId } })
    },

    // 获取关注数量
    getCount(userId) {
      return api.get('/follows/count', { params: { user_id: userId } })
    },

    // 获取粉丝列表
    getFollowers(userId, limit = 20, offset = 0) {
      return api.get('/follows/followers', { params: { user_id: userId, limit, offset } })
    },

    // 获取关注列表
    getFollowing(userId, limit = 20, offset = 0) {
      return api.get('/follows/following', { params: { user_id: userId, limit, offset } })
    },

    // 获取我的关注/粉丝列表
    getMyFollows(listType = 'following', limit = 20, offset = 0) {
      return api.get('/follows/my', { params: { list_type: listType, limit, offset } })
    }
  },

  // 评论功能
  comments: {
    // 创建评论
    create(data) {
      return api.post('/comments', data)
    },

    // 获取评论列表
    getList(params) {
      return api.get('/comments/list', { params })
    },

    // 获取回复列表
    getReplies(params) {
      return api.get('/comments/replies', { params })
    },

    // 获取评论详情
    get(commentId) {
      return api.get(`/comments/${commentId}`)
    },

    // 更新评论
    update(commentId, data) {
      return api.put(`/comments/${commentId}`, data)
    },

    // 删除评论
    delete(commentId) {
      return api.delete(`/comments/${commentId}`)
    },

    // 点赞评论
    like(commentId) {
      return api.post(`/comments/${commentId}/like`)
    },

    // 取消点赞评论
    unlike(commentId) {
      return api.delete(`/comments/${commentId}/like`)
    },

    // 获取我的评论列表
    getMyList(targetType = null, page = 1, pageSize = 20) {
      const params = { page, page_size: pageSize }
      if (targetType) {
        params.target_type = targetType
      }
      return api.get('/comments/my/list', { params })
    }
  },

  // 个人主页
  profile: {
    // 获取用户资料
    getProfile(userId) {
      return api.get(`/profile/${userId}`)
    },

    // 获取自己的资料
    getMyProfile() {
      return api.get('/profile')
    },

    // 更新资料
    updateProfile(data) {
      return api.put('/profile', data)
    },

    // 上传头像
    uploadAvatar(file, onProgress) {
      const formData = new FormData()
      formData.append('avatar', file)

      return api.post('/profile/avatar', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(percent)
          }
        }
      })
    },

    // 删除头像
    deleteAvatar() {
      return api.delete('/profile/avatar')
    },

    // 获取用户内容
    getUserContent(userId, params) {
      return api.get(`/profile/${userId}/posts`, { params })
    },

    // 获取用户点赞
    getUserLikes(userId, params) {
      return api.get(`/profile/${userId}/likes`, { params })
    },

    // 获取统计信息
    getProfileStats(userId) {
      return api.get(`/profile/${userId}/stats`)
    }
  },

  // 树洞功能
  treehole: {
    // 获取树洞列表
    getList(params) {
      return api.get('/treehole/list', { params })
    },

    // 发布树洞
    create(data) {
      return api.post('/treehole', data)
    },

    // 获取树洞详情
    get(post_id) {
      return api.get(`/treehole/${post_id}`)
    },

    // 删除树洞
    delete(post_id) {
      return api.delete(`/treehole/${post_id}`)
    },

    // 获取我的树洞列表
    getMyList(params) {
      return api.get('/treehole/my/list', { params })
    }
  },

  // 发现页面功能
  discovery: {
    // 获取推荐内容
    getRecommendations(params) {
      return api.get('/discovery/recommend', { params })
    },

    // 获取热门内容
    getHotList(params) {
      return api.get('/discovery/hot', { params })
    },

    // 搜索内容
    search(params) {
      return api.get('/discovery/search', { params })
    },

    // 获取分类列表
    getCategories() {
      return api.get('/discovery/categories')
    },

    // 获取标签列表
    getTags(params) {
      return api.get('/discovery/tags', { params })
    },

    // 获取信息流
    getFeed(params) {
      return api.get('/discovery/feed', { params })
    },

    // 获取推荐配置
    getConfig() {
      return api.get('/discovery/config')
    }
  },

  // 消息功能
  messages: {
    // 发送私信
    send(data) {
      return api.post('/messages/send', data)
    },

    // 获取消息列表
    getList(params) {
      return api.get('/messages/list', { params })
    },

    // 获取私信会话列表
    getConversationList(params) {
      return api.get('/messages/conversation/list', { params })
    },

    // 获取与指定用户的私信记录
    getConversationMessages(userId, params) {
      return api.get(`/messages/conversation/${userId}`, { params })
    },

    // 获取消息详情
    get(messageId) {
      return api.get(`/messages/${messageId}`)
    },

    // 批量标记已读
    markRead(data) {
      return api.post('/messages/mark-read', data)
    },

    // 标记为未读
    markUnread(messageId) {
      return api.post(`/messages/mark-unread?message_id=${messageId}`)
    },

    // 批量删除
    delete(data) {
      return api.post('/messages/delete', data)
    },

    // 一键已读
    readAll(params) {
      return api.post('/messages/read-all', null, { params })
    },

    // 获取未读数量
    getUnreadCount() {
      return api.get('/messages/unread/count')
    },

    // 发送系统通知
    sendSystemNotify(data) {
      return api.post('/messages/system-notify', data)
    },

    // 发送互动通知
    sendInteractionNotify(data) {
      return api.post('/messages/interaction-notify', data)
    }
  },

  // 公告功能
  announcements: {
    // 获取公告列表
    getList(params) {
      return api.get('/announcements/list', { params })
    },

    // 获取公告详情
    get(announcementId) {
      return api.get(`/announcements/${announcementId}`)
    }
  }
}
