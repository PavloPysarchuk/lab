src=open("/home/pavlo/lab/tts_test/stage2.py").read()
cut=src.index("kokoro peak VRAM")
head=src[:src.rindex("print(",0,cut)]
head+='print("kokoro peak VRAM %.2f GiB"%(torch.cuda.max_memory_allocated(DEV)/2**30),flush=True)\n'
head+='json.dump(res,open(OUT+"/stage2.json","w"),indent=1)\n'
head+='print("STAGE2A_DONE")\n'
open("/home/pavlo/lab/tts_test/stage2a.py","w").write(head)
print("wrote",len(head))
