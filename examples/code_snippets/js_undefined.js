/**
 * 处理数据并提取属性
 * @param {Array} data - 要处理的数据数组
 * @returns {Array} - 处理后的结果
 */
function processData(data) {
  // 检查数据是否存在
  if (!data) {
    return [];
  }

  // 从数据中提取value属性
  return data.map((item) => item.value);
}

// 测试函数
const testData = null; // 这会导致错误，应该传入数组
const result = processData(testData);
