import asyncio 
import asyncpg 
async def test(): 
    try: 
        conn = await asyncpg.connect(host='localhost',port=5432,user='postgres',password='claim360pass',database='claim360') 
        print('SUCCESS!') 
        await conn.close() 
    except Exception as e: 
        print('FAILED:', e) 
asyncio.run(test()) 
