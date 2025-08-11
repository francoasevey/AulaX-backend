# test_atlas_now.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test_connection():
    """Test inmediato de conexión Atlas"""
    
    connection_string = "mongodb+srv://francoasevey:2kDokCGxhxXoFqRl@francocluster.cw9qc37.mongodb.net/?retryWrites=true&w=majority"
    
    try:
        print("🔗 Conectando a Atlas...")
        client = AsyncIOMotorClient(connection_string, serverSelectionTimeoutMS=5000)
        
        # Test ping
        await client.admin.command('ping')
        print("✅ ¡Conexión exitosa!")
        
        # Test database
        db = client.aula_x
        result = await db.test.insert_one({"test": "AULA X works!", "status": "success"})
        print(f"✅ Test de escritura: {result.inserted_id}")
        
        # Cleanup
        await db.test.delete_one({"_id": result.inserted_id})
        client.close()
        
        print("🎉 ¡ATLAS FUNCIONANDO PERFECTAMENTE!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())