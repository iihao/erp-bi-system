import api from './index'

/**
 * 消息功能 API
 */
export default {
  /**
   * 发送私信
   * @param {Object} data - 消息数据
   * @param {number} data.receiver_id - 接收者 ID
   * @param {string} data.title - 消息标题
   * @param {string} data.content - 消息内容
   * @returns {Promise}
   */
  send(data) {
    return api.messages.send(data)
  },

  /**
   * 获取消息列表
   * @param {Object} params - 查询参数
   * @param {string} [params.message_type] - 消息类型 (private|system|interaction)
   * @param {number} [params.page=1] - 页码
   * @param {number} [params.page_size=20] - 每页数量
   * @returns {Promise}
   */
  getList(params) {
    return api.messages.getList(params)
  },

  /**
   * 获取私信会话列表
   * @param {number} [page=1] - 页码
   * @param {number} [pageSize=20] - 每页数量
   * @returns {Promise}
   */
  getConversationList(page = 1, pageSize = 20) {
    return api.messages.getConversationList({ page, page_size: pageSize })
  },

  /**
   * 获取与指定用户的私信记录
   * @param {number} userId - 对方用户 ID
   * @param {number} [page=1] - 页码
   * @param {number} [pageSize=50] - 每页数量
   * @returns {Promise}
   */
  getConversationMessages(userId, page = 1, pageSize = 50) {
    return api.messages.getConversationMessages(userId, { page, page_size: pageSize })
  },

  /**
   * 获取单条消息详情
   * @param {number} messageId - 消息 ID
   * @returns {Promise}
   */
  get(messageId) {
    return api.messages.get(messageId)
  },

  /**
   * 批量标记消息为已读
   * @param {number[]} messageIds - 消息 ID 列表
   * @returns {Promise}
   */
  markAsRead(messageIds) {
    return api.messages.markRead({ message_ids: messageIds, operation: 'read' })
  },

  /**
   * 标记消息为未读
   * @param {number} messageId - 消息 ID
   * @returns {Promise}
   */
  markAsUnread(messageId) {
    return api.messages.markUnread(messageId)
  },

  /**
   * 批量删除消息
   * @param {number[]} messageIds - 消息 ID 列表
   * @returns {Promise}
   */
  delete(messageIds) {
    return api.messages.delete({ message_ids: messageIds, operation: 'delete' })
  },

  /**
   * 一键已读所有消息
   * @param {string|null} messageType - 消息类型（可选）
   * @returns {Promise}
   */
  readAll(messageType = null) {
    return api.messages.readAll(messageType ? { message_type: messageType } : {})
  },

  /**
   * 获取未读消息数量
   * @returns {Promise}
   */
  getUnreadCount() {
    return api.messages.getUnreadCount()
  },

  /**
   * 发送系统通知（管理员）
   * @param {Object} data - 通知数据
   * @param {number} data.receiver_id - 接收者 ID（0 表示广播）
   * @param {string} data.title - 通知标题
   * @param {string} data.content - 通知内容
   * @param {string} [data.priority='normal'] - 优先级
   * @returns {Promise}
   */
  sendSystemNotify(data) {
    return api.messages.sendSystemNotify(data)
  },

  /**
   * 发送互动通知
   * @param {Object} data - 通知数据
   * @param {number} data.receiver_id - 接收者 ID
   * @param {string} data.source_type - 来源类型 (like|comment|follow)
   * @param {number} data.source_id - 来源 ID
   * @param {string} data.content - 通知内容
   * @returns {Promise}
   */
  sendInteractionNotify(data) {
    return api.messages.sendInteractionNotify(data)
  },

  /**
   * 获取公告列表
   * @param {Object} params - 查询参数
   * @param {string} [params.status_filter='published'] - 状态
   * @param {number} [params.page=1] - 页码
   * @param {number} [params.page_size=10] - 每页数量
   * @returns {Promise}
   */
  getAnnouncements(params) {
    return api.announcements.getList(params)
  },

  /**
   * 获取公告详情
   * @param {number} announcementId - 公告 ID
   * @returns {Promise}
   */
  getAnnouncement(announcementId) {
    return api.announcements.get(announcementId)
  }
}
