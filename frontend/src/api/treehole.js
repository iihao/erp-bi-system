import api from './index'

/**
 * 树洞功能 API
 */
export default {
  /**
   * 获取树洞列表
   * @param {Object} params - 查询参数
   * @param {number} [params.page=1] - 页码
   * @param {number} [params.page_size=20] - 每页数量
   * @param {string} [params.sort_by='created_at'] - 排序字段：created_at-时间，hot-热度
   * @returns {Promise}
   */
  getList(params) {
    return api.treehole.getList(params)
  },

  /**
   * 发布树洞
   * @param {Object} data - 树洞数据
   * @param {string} data.content - 树洞内容
   * @param {string} [data.title] - 可选标题
   * @returns {Promise}
   */
  create(data) {
    return api.treehole.create(data)
  },

  /**
   * 获取树洞详情
   * @param {number} post_id - 树洞 ID
   * @returns {Promise}
   */
  get(post_id) {
    return api.treehole.get(post_id)
  },

  /**
   * 删除树洞
   * @param {number} post_id - 树洞 ID
   * @returns {Promise}
   */
  delete(post_id) {
    return api.treehole.delete(post_id)
  },

  /**
   * 获取我的树洞列表
   * @param {Object} params - 查询参数
   * @param {number} [params.page=1] - 页码
   * @param {number} [params.page_size=20] - 每页数量
   * @returns {Promise}
   */
  getMyList(params) {
    return api.treehole.getMyList(params)
  }
}
