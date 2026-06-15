import { useMainStore } from '@/stores/main';

export default defineNuxtPlugin((nuxtApp) => {
  const store = useMainStore();

  function showAlert(alert_type, alert_msg, alert_to) {
    store.setAlert({ type: alert_type, msg: alert_msg, to: alert_to });
    if (alert_type === 'success') {
      setTimeout(() => {
        store.closeAlert();
      }, 1300);
    }
  }

  async function backend(url, options) {
    if (url === undefined) {
      throw 'url is undefined ';
    }
    var args = {
      mode: 'cors', redirect: 'follow', credentials: 'include',
    };

    const config = useRuntimeConfig();
    let server = '';
        
    if (process.server) {
      const headers = useRequestHeaders(['cookie', 'host', 'x-forwarded-for', 'x-forwarded-proto', 'x-scheme']);
      server = config.public.api_url;
      args.headers = {
        'cookie': headers.cookie,
        'X-Forwarded-Host': headers.host,
        'X-Forwarded-For': headers['x-forwarded-for'],
        'X-Forwarded-Proto': headers['x-forwarded-proto'],
        'X-Scheme': headers['x-scheme'],
      };
    } else {
      server = window.location.origin;
    }

    var full_url = server + '/api' + url;

    if (options !== undefined) {
      Object.assign(args, options);
    }

    try {
      const rsp = await fetch(full_url, args);
      var msg = '';
      if (rsp.status === 413) {
        msg = '服务器响应了413异常状态码。<br/>可能是上传的文件过大，超过了服务器设置的上传大小。';
        showAlert('error', msg);
        throw msg;
      }

      if (rsp.status === 502) {
        msg = '服务器正在启动中...';
        showAlert('info', msg);
        throw msg;
      }

      if (rsp.status !== 200) {
        msg = '服务器异常，状态码: ' + rsp.status + '<br/>请查阅服务器日志:<br/>talebook.log';
        showAlert('error', msg);
        throw msg;
      }

      let data;
      try {
        data = await rsp.json();
      } catch (err) {
        msg = '服务器异常，响应非JSON<br/>请查阅服务器日志:<br/>talebook.log';
        showAlert('error', msg);
        throw msg;
      }

      if (data.err === 'not_installed') {
        console.log('[Talebook] Redirecting to /install');
        await nuxtApp.runWithContext(() => navigateTo('/install', { redirectCode: 302 }));
      } else if (data.err === 'not_invited') {
        const route = useRoute();
        var next = route.fullPath;
        next = next ? '?next=' + next : '';
        if (route.path !== '/welcome') {
          await nuxtApp.runWithContext(() => navigateTo('/welcome' + next, { redirectCode: 302 }));
        }
      } else if (data.err === 'user.need_login') {
        await nuxtApp.runWithContext(() => navigateTo('/login', { redirectCode: 302 }));
      } else if (data.err === 'exception') {
        store.setAlert({ type: 'error', msg: data.msg, to: null });
      }
      return data;

    } catch (e) {
      // console.error(e)
      throw e;
    }
  }

  // 流式请求：返回 NDJSON 异步迭代器，调用方用 for await 逐条消费。
  // 约定首行为 meta（total/title/err 等），后续行为数据项。
  async function* backend_stream(url, options) {
    if (url === undefined) {
      throw 'url is undefined ';
    }
    var args = {
      mode: 'cors', redirect: 'follow', credentials: 'include',
    };

    const config = useRuntimeConfig();
    const server = import.meta.server ? config.public.api_url : window.location.origin;

    if (options !== undefined) {
      Object.assign(args, options);
    }

    const rsp = await fetch(server + '/api' + url, args);
    if (!rsp.ok) {
      throw new Error('stream request failed: ' + rsp.status);
    }
    yield* parseNdjson(rsp);
  }

  return {
    provide: {
      alert: showAlert,
      backend: backend,
      backend_stream: backend_stream
    }
  };
});

// 解析 NDJSON（换行分隔的 JSON）流：逐行 yield 已解析的对象，跳过空行与非法行，
// 并正确拼接跨 chunk 被截断的行。单独导出以便单元测试。
export async function* parseNdjson(response) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop();

    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        yield JSON.parse(line);
      } catch (e) {
        // 跳过不完整/非法的行
      }
    }
  }
}
