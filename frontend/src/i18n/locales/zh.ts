// 段功能：中文文案资源（M1 基建 + M2 扩展）
// 说明：与 en.ts 的 key 完全一致，保证双语一一对应。
//       M2 新增 home / models / modelDetail / articles 命名空间，覆盖首页与列表/详情页文案。
const zh = {
  nav: {
    home: "首页",
    models: "车型",
    news: "资讯",
  },
  model: {
    detail: "车型详情",
  },
  news: {
    detail: "资讯详情",
  },
  common: {
    comingSoon: "页面建设中（M1 占位）",
    loading: "加载中…",
    error: "加载失败，请重试",
  },
  brand: {
    name: "冠驭名车 REGALIA MOTORS",
  },
  // 首页
  home: {
    heroTitle: "尊享豪华座驾",
    heroSubtitle: "聚合全球顶级品牌，一站式选车",
    explore: "立即探索",
    brands: "品牌",
    recommended: "推荐车型",
    latestNews: "最新资讯",
    viewAll: "查看全部",
  },
  // 车型列表
  models: {
    title: "车型",
    filter: "筛选",
    all: "全部",
    segment: "级别",
    fuel: "能源",
    price: "价格",
    sort: "排序",
    sortDefault: "默认",
    sortPrice: "价格升序",
    sortLaunch: "最新上市",
    sortHeat: "热门推荐",
    results: "共 {{count}} 款",
    noResult: "暂无符合条件的车型",
    guidePrice: "指导价",
  },
  // 车型详情
  modelDetail: {
    gallery: "图库",
    trims: "配置版本",
    colors: "颜色",
    dealers: "在售经销商",
    finance: "金融方案",
    financeCta: "估算月供",
    body: "车身尺寸",
    length: "长",
    width: "宽",
    height: "高",
    wheelbase: "轴距",
    trunk: "后备箱",
    back: "返回列表",
    notFound: "车型不存在或已下架",
    actions: "选车与咨询",
    configure: "立即配置",
  },
  // 资讯
  articles: {
    title: "资讯",
    noResult: "暂无资讯",
    back: "返回列表",
    notFound: "资讯不存在",
  },
  // M3 配置器
  configurator: {
    title: "车型配置",
    start: "开始配置",
    basePrice: "基础价",
    total: "预估总价",
    stock: "库存状态",
    stockInStock: "现车",
    stockPreorder: "预订",
    stockEol: "停产",
    leadTime: "预计交付",
    days: "天",
    defaultTag: "默认",
    next: "下一步",
    prev: "上一步",
    finish: "完成配置",
    toLead: "提交试驾留资",
    summary: "配置摘要",
    requiredHint: "请先选择必选项",
  },
  // M3 对比
  compare: {
    title: "车型对比",
    empty: "请选择至少 2 款车型进行对比",
    addHint: "在车型列表勾选「对比」后点击查看",
    clear: "清空",
    guidePrice: "指导价",
    fuel: "能源",
    segment: "级别",
    body: "车身尺寸",
    power: "动力",
    trims: "配置版本数",
    close: "关闭",
  },
  // M3 金融计算器
  finance: {
    title: "金融计算器",
    term: "贷款期数",
    downPayment: "首付比例",
    monthly: "预计月供",
    totalInterest: "总利息",
    calculate: "计算月供",
    hint: "等额本息估算，实际以金融方案为准",
    product: "方案",
  },
  // M3 留资（试驾 / 询价）
  lead: {
    testDriveTitle: "预约试驾",
    inquiryTitle: "在线咨询 / 询价",
    name: "姓名",
    phone: "手机号",
    city: "城市",
    model: "意向车型",
    preferredTime: "期望时间",
    remark: "备注",
    intent: "询价类型",
    intentTradeIn: "置换",
    intentFinance: "金融",
    intentStock: "现车",
    submit: "提交",
    success: "提交成功，顾问将尽快与您联系",
    error: "提交失败，请稍后重试",
    required: "请填写姓名与手机号",
    invalidPhone: "手机号格式不正确",
  },
};

export default zh;
