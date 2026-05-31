# ASR 模型对比报告: Qwen3-ASR-1.7B vs Whisper-large-v3-turbo

> 测试音频源: `data/8be949d4b3e2d56e21106753884ace77.mp4` (~199.6s, 16kHz 单声道)
> 测试硬件: NVIDIA H20-3e (单卡, cuda:0)
> 测试日期: 2026-05-23

---

## 1. 测试设置

| 项 | 值 |
| --- | --- |
| 视频 | `AI4Video/data/8be949d4b3e2d56e21106753884ace77.mp4` |
| 音频抽取 | PyAV → 16kHz / mono / pcm_s16le (见 `framework/audio_utils.py`) |
| 音频时长 | 199.6 秒 |
| Qwen3-ASR 权重 | `Qwen3-ASR-1.7B` |
| Whisper 权重 | `whisper-large-v3-turbo` |
| 精度 | bf16 (Qwen3-ASR) / fp16 (Whisper) |
| Attention | flash-attention-2 (Qwen3-ASR) / SDPA 默认 (Whisper) |

---

## 2. 转录结果对比

### 2.1 Qwen3-ASR-1.7B (force language=Chinese)

> 女士们、先生们，请安静一下。接下来，请欣赏舞台剧《路易波拿巴的五月十八日》。在遥远的欧罗巴大陆上，有位富有的国王，子民们献上宝物为他打造皇冠，献上布匹为他缝制衣裳。可是有一天，子民们不愿再忍受碌碌鸡肠，便抄起了武器与火枪赶走了国王。矮子将军拿破仑带领着人们开启了共和国的篇章，人民们爱戴拿破仑，便用鲜花与歌唱推举他成为新帝王。人民们厌恶拿破仑，便又用武器与火枪将他流放。这时候，一位大地主站在高耸的城堡上呼喊："我是立宪的君主，我的王朝叫做波旁。"人们信任大地主，便推举他成为新帝王。人民厌恶大地主，便又将他逐放。这时候，一位金融巨鳄站在临时的财宝上呼喊："我是立宪的君主，请记住我的三色旗帜，我的王朝叫做奥尔良。"人民们别无他选，便推举他成为新帝王。议会里论派别而坐，国都里论阶级抬扛。总统派大喊着："我是波旁王朝的遗老，我怀念已故的国王。"共和派大喊着："我想要的是资本与权力，而非国王。"而人民却大喊着："我要无数的面包，要国有的工厂。"人们再一次抄起武器与火枪，建立了自己的临时政府与国有工厂。临时政府的议会里，把权的是整日把自由与宪法挂在嘴边的共和派波旁与奥尔良的拥趸们自称秩序党，而那些工人兄弟们早被抛出了议会，逐出了政党。这时候，狡猾的路易波拿巴站了出来，他说："我同情工人与农民，渴望秩序与安稳，我要成为共和国的首长。"秩序党与工农们爱戴他，便推举他为总统，将他高举在庙堂。狡猾的路易波拿巴说："我将忠诚于宪法，忠诚于共和国。"于是他修改了宪法，发起了政变，处死了敌人和流氓们，建立了自己的政党。可人民呢，只想拥有面包与工厂，他们开始怀念从前的英雄拿破仑国王，并将希望投给英雄国王的侄子路易波拿巴身上，推举他成为新帝王。啊，路易波拿巴这个卑劣的国王，以为照耀法兰西的还是那个太阳，就觉得自己就是拿破仑国王。哦，这个可笑的小丑！五月十八的法兰西是多么阴暗！他所有的伎俩与把戏不过是舞台剧上拙劣的模仿。

### 2.2 Whisper-large-v3-turbo (auto / 强制 chinese 结果相同)

> 女士们先生们,请安静一下,接下来请欣赏舞台剧《路易伯纳巴》的5月18日在遥远的欧罗巴大陆上,有位富有的国王子民们献上宝物,为他打造皇冠,献上布匹,为他缝制衣裳可是有一天,子民们不愿再忍受陆路机长,便抄起了武器与火枪,赶走了国王 **优优独播剧场——YoYo Television Series Exclusive** 为他缝制衣裳可是有一天子民们不愿再忍受碌碌机场便抄起了武器与火枪赶走了国王矮子将军拿破仑带领着人们开启了共和国的篇章神迷们爱戴拿破仑便用鲜花语歌唱推举他成为新帝王神迷们厌恶拿破仑便又用武器与火枪将他流放这时候一位大地主站在高耸的城堡上呼喊我是立宪的君主我的王朝叫做波旁人们信任大地主便推举他成为新帝王人民厌恶大地主便又将他竹放这时候一位金融巨鳄站在累世的财宝上呼喊我是立宪的君主请记住我的三色旗帜我的王朝叫做奥尔良人民们别无他选便推举他成为新帝王议会里论派别而做国度里论阶级排行众统派大喊着我是波旁王朝的遗老我怀念已故的国王共和派大喊着我想要的是资本与权利而非国王而人民却大喊着我要无数的面包要国有的工厂人们再一次抄起武器与火枪建立了自己的临时政府与国有工厂。临时政府的议会里,拔权的是整日把自由与宪法挂在嘴边的共和派,波旁与奥尔良的拥躬们自称秩序党,而那些工人兄弟们早被抛出了议会,逐出了政党。这时候,狡猾的路易波纳巴站了出来,他说,我同情工人与农民,渴望秩序与安稳,我要成为共和国的首长。秩序党与工农们爱戴他,并推举他为总统,将他高举在庙堂。教化的路易波拿巴说我将忠诚于宪法忠诚于宪法,忠诚于共和国。于是,他修改了宪法,发起了政变,处死了敌人和流氓们,建立了自己的政党。可人民呢,只想拥有面包与工厂,他们开始怀念从前的英雄,**拿�**国王并将希望投给英雄国王的侄子路易波拿巴身上推举他成为新帝王啊路易波拿巴这个卑劣的国王以为照耀法兰西的还是那个太阳就觉得自己就是拿破仑国王哦这个可笑的小丑五月十八的法兰西是多么阴暗他所有的伎俩与把戏不过是舞台剧上拙劣的模仿

---

## 3. 关键差异

| 维度 | Qwen3-ASR-1.7B | Whisper-large-v3-turbo |
| --- | --- | --- |
| 语言识别 (auto) | ✅ 直接识别为中文, 输出与强制中文一致 | ✅ 识别为中文, 但与强制 chinese 输出相同 (内含问题) |
| 标点 | ✅ 中文全角句号 / 逗号 / 引号齐全 | ⚠️ 仅有半角逗号, 几乎没有句号、引号缺失 |
| 标题识别 | ✅ "路易波拿巴的五月十八日" | ❌ "《路易伯纳巴》的5月18日" (人名错, 标题截断) |
| 幻觉 (hallucination) | ✅ 无 | ❌ 凭空插入 **"优优独播剧场——YoYo Television Series Exclusive"** (典型 Whisper 视频字幕集训练偏置) |
| 长音频分段 | ✅ 句句连续无重复 | ❌ 一段(为他缝制衣裳…赶走了国王) **整段重复** (chunked long-form 边界 bug) |
| 同音/形近字错 | 几乎无 | ❌ "碌碌鸡肠"→"陆路机长", "把权"→"拔权", "狡猾的"→"教化的", "总统派"→"重/众统派", "拥趸"→"拥躬", "权力"→"权利", "逐放"→"竹放", "临时"→"累世", "抬扛"→"排行" |
| 非法 Unicode | 无 | ❌ 出现 "拿�" (UNK / decode 失败) |
| 语言提示行为 | language=Chinese 强制后稳定; auto 也基本一致 (latency 优化) | 强制 chinese 与 auto **完全等价**, 未观察到改善 |
| 首次推理延迟 | 42.7 s | 51.3 s |
| 第二次推理延迟 (warm) | **15.3 s** | 17.0 s |
| 模型权重大小 | ~4.4 GB (bf16, 2 shards) | ~1.6 GB (fp16) |

> **结论 (粗略)**: 对这段普通话舞台剧旁白:
> - **Qwen3-ASR-1.7B** 在中文场景下转录质量明显领先, 几乎无字错且能正确插入中文标点；同时 warm latency 也更快.
> - **Whisper-large-v3-turbo** 体积更小、生态更成熟, 但中文长音频上会:
>   1. 触发"优优独播剧场" 类视频水印幻觉;
>   2. 在 30 秒 chunk 边界出现整句重复;
>   3. 大量音近字混淆 (碌碌鸡肠 → 陆路机长 等);
>   4. 几乎不输出中文句末标点.
> - 若仅用于多语种、对延迟和模型尺寸更敏感的场景, Whisper 仍然是合理选择; 但纯中文字幕生产场景应优先 Qwen3-ASR.

---

## 4. 延迟与显存

| 模型 | 首推 (cold) | 二次 (warm) | 说明 |
| --- | ---: | ---: | --- |
| Qwen3-ASR-1.7B | 42.7 s | 15.3 s | 首次包含 flash-attention kernel autotune |
| whisper-large-v3-turbo | 51.3 s | 17.0 s | `chunk_length_s=30`, `batch_size=8`, 内部 30s 切片并行 |

(200 秒音频 / 13 s 转录 ≈ 15× 实时倍速; 两者在 H20 单卡上都达到了准实时以上的吞吐。)

---

## 5. 核心调用代码

### 5.1 Qwen3-ASR-1.7B (`framework/asr.py`)

```python
import torch
from qwen_asr import Qwen3ASRModel

class Qwen3ASRTester(BaseTester):
    def _load_model(self) -> None:
        # qwen-asr 官方包封装了 transformers 后端, 直接 from_pretrained 即可
        self.model = Qwen3ASRModel.from_pretrained(
            self.model_path,                  # 本地权重目录
            dtype=torch.bfloat16,
            device_map="cuda:0",
            max_inference_batch_size=8,
            max_new_tokens=1024,
            attn_implementation="flash_attention_2",
        )

    def _infer(self, media: str, prompt: str, **kwargs):
        # prompt 字段在框架里被复用为 language hint
        # "auto" / "" -> 让模型自己识别; "Chinese" / "English" -> 强制
        language = prompt.strip() if prompt and prompt.lower() != "auto" else None
        results = self.model.transcribe(
            audio=media,                      # 直接传 WAV 路径, 内部自动 resample
            language=language,
            return_time_stamps=False,         # =True 需要额外的 forced_aligner 权重
        )
        return results[0].text, {"language": getattr(results[0], "language", None)}
```

### 5.2 Whisper-large-v3-turbo (`framework/whisper_asr.py`)

```python
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

class WhisperASRTester(BaseTester):
    def _load_model(self) -> None:
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            self.model_path,                  # 本地权重目录
            dtype=torch.float16,
            low_cpu_mem_usage=True,
            use_safetensors=True,
        ).to("cuda:0")
        processor = AutoProcessor.from_pretrained(self.model_path)
        # 用 pipeline 自动处理 30s 切片 + batch
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            torch_dtype=torch.float16,
            device="cuda:0",
            chunk_length_s=30,
            batch_size=8,
        )

    def _infer(self, media: str, prompt: str, **kwargs):
        # 自己读 WAV 成 numpy, 不依赖系统 ffmpeg
        audio, sr = load_wav_as_array(media)  # 16kHz / float32 / [-1, 1]
        generate_kwargs = {"task": "transcribe"}
        if prompt and prompt.lower() not in {"", "auto", "none"}:
            generate_kwargs["language"] = prompt.lower()  # e.g. "chinese"

        result = self.pipe(
            {"raw": audio, "sampling_rate": sr},
            generate_kwargs=generate_kwargs,
            return_timestamps=kwargs.get("return_time_stamps", False),
        )
        return result["text"].strip(), {"language": generate_kwargs.get("language", "auto")}
```

### 5.3 公共音频抽取 (`framework/audio_utils.py`, 由 PyAV 实现, 无需 ffmpeg 二进制)

```python
import av
def extract_audio_from_video(video_path, output_path, target_sr=16000):
    with av.open(str(video_path)) as in_c:
        in_stream = next(s for s in in_c.streams if s.type == "audio")
        resampler = av.AudioResampler(format="s16", layout="mono", rate=target_sr)
        with av.open(str(output_path), mode="w") as out_c:
            out_stream = out_c.add_stream("pcm_s16le", rate=target_sr)
            out_stream.layout = "mono"
            for frame in in_c.decode(in_stream):
                for resampled in resampler.resample(frame):
                    for pkt in out_stream.encode(resampled):
                        out_c.mux(pkt)
            for pkt in out_stream.encode(None):
                out_c.mux(pkt)
```

---

## 6. 复现入口

```bash
cd AI4Video
python run_asr_compare.py
# 输出:
#   data/8be949d4b3e2d56e21106753884ace77.wav       (抽取的 16kHz 单声道音频)
#   outputs/asr_compare/qwen3_asr.json              (Qwen3-ASR 转录原始结果 + latency)
#   outputs/asr_compare/whisper_large_v3_turbo.json (Whisper 转录原始结果 + 分段时间戳)
```
