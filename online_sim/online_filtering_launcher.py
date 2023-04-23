import os
import sys
import asyncio

MAX_PROCESSES = 14

raw_data_path = '/remote_disk/raw_data'
dst_path = '/home/dean/PycharmProjects/cwnd_clgo_classifier/classification_data/physical data'
folders_list = os.listdir(raw_data_path)

async def process_folder(folder, sem):
    async with sem:  # controls/allows running 10 concurrent subprocesses at a time
        proc = await asyncio.create_subprocess_exec(sys.executable, 'online_filtering.py', raw_data_path, dst_path,
                                                    folder)
        await proc.wait()


async def main():
    sem = asyncio.Semaphore(MAX_PROCESSES)
    await asyncio.gather(*[process_folder(folder, sem) for folder in folders_list])


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
