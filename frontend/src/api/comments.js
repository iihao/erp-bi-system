import api from './index'

/**
 * 评论功能 API
 */
export default {
  /**
   * 创建评论
   * @param {Object} data - 评论数据
   * @param {string} data.target_type - 目标类型 (post|report)
   * @param {number} data.target_id - 目标 ID
   * @param {string} data.content - 评论内容
   * @param {number} [data.parent_id=0] - 父评论 ID（回复评论时使用）
   * @returns {Promise}
   */
  create(data) {
    return api.comments.create(data)
  },

  /**
   * 获取评论列表
   * @param {Object} params - 查询参数
   * @param {string} params.target_type - 目标类型
   * @param {number} params.target_id - 目标 ID
   * @param {number} [params.page=1] - 页码
   * @param {number} [params.page_size=20] - 每页数量
   * @param {string} [params.sort_by='created_at'] - 排序字段
   * @returns {Promise}
   */
  getList(params) {
    return api.comments.getList(params)
  },

  /**
   * 获取回复列表
   * @param {Object} params - 查询参数
   * @param {number} params.parent_id - 父评论 ID
   * @param {number} [params.page=1] - 页码
   * @param {number} [params.page_size=20] - 每页数量
   * @returns {Promise}
   */
  getReplies(params) {
    return api.comments.getReplies(params)
  },

  /**
   * 获取评论详情
   * @param {number} commentId - 评论 ID
   * @returns {Promise}
   */
  get(commentId) {
    return api.comments.get(commentId)
  },

  /**
   * 更新评论
   * @param {number} commentId - 评论 ID
   * @param {Object} data - 更新数据
   * @param {string} data.content - 新的评论内容
   * @returns {Promise}
   */
  update(commentId, data) {
    return api.comments.update(commentId, data)
  },

  /**
   * 删除评论
   * @param {number} commentId - 评论 ID
   * @returns {Promise}
   */
  delete(commentId) {
    return api.comments.delete(commentId)
  },

  /**
   * 点赞评论
   * @param {number} commentId - 评论 ID
   * @returns {Promise}
   */
  like(commentId) {
    return api.comments.like(commentId)
  },

  /**
   * 取消点赞评论
   * @param {number} commentId - 评论 ID
   * @returns {Promise}
   */
  unlike(commentId) {
    return api.comments.unlike(commentId)
  },

  /**
   * 获取我的评论列表
   * @param {string|null} targetType - 目标类型（可选）
   * @param {number} [page=1] - 页码
   * @param {number} [pageSize=20] - 每页数量
   * @returns {Promise}
   */
  getMyList(targetType = null, page = 1, pageSize = 20) {
    return api.comments.getMyList(targetType, page, pageSize)
  }
}
