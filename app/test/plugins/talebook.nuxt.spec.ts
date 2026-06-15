import { describe, it, expect } from 'vitest';
import { parseNdjson } from '~/plugins/talebook';

// 构造一个最小 Response：body.getReader() 按给定的 chunk 序列依次吐出数据。
// 用于验证 parseNdjson 的逐行解析与跨 chunk 拼接逻辑。
function fakeResponse(chunks: string[]) {
    const encoder = new TextEncoder();
    let i = 0;
    return {
        body: {
            getReader() {
                return {
                    read() {
                        if (i < chunks.length) {
                            return Promise.resolve({ done: false, value: encoder.encode(chunks[i++]) });
                        }
                        return Promise.resolve({ done: true, value: undefined });
                    }
                };
            }
        }
    };
}

async function collect(gen: AsyncGenerator) {
    const out = [];
    for await (const x of gen) out.push(x);
    return out;
}

describe('parseNdjson', () => {
    it('逐行解析完整的 NDJSON 流', async () => {
        const res = fakeResponse(['{"total":2}\n{"id":1}\n{"id":2}\n']);
        expect(await collect(parseNdjson(res))).toEqual([{ total: 2 }, { id: 1 }, { id: 2 }]);
    });

    it('拼接跨 chunk 被截断的行', async () => {
        const res = fakeResponse(['{"to', 'tal":2}\n{"id":', '1}\n']);
        expect(await collect(parseNdjson(res))).toEqual([{ total: 2 }, { id: 1 }]);
    });

    it('跳过空行与非法 JSON', async () => {
        const res = fakeResponse(['{"id":1}\n\nnot-json\n{"id":2}\n']);
        expect(await collect(parseNdjson(res))).toEqual([{ id: 1 }, { id: 2 }]);
    });
});
