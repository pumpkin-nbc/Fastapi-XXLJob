# 部署

请使用生产级 ASGI Server，并只暴露配置的路由前缀。每个 ASGI Worker 在自身进程中维护一个注册线程；本包不进行跨进程 Leader 选举。

请配置 HTTPS、非空 Token、网络访问控制、有限超时，以及 Admin 可访问的执行器地址。启用注销时，正常 lifespan 关闭会执行幂等注销。
